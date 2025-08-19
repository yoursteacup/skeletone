import asyncio
import inspect
import logging
import logging.config
import secrets
from collections import deque
from datetime import datetime, timezone
from typing import Deque, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_logs import ApplicationLogs
from app.services.sessionmaking import async_session
from app.utils.enums import LogLevel
from app.utils.log_config import get_log_config

LOGGING_LEVELS = {
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.DEBUG: logging.DEBUG,
}


class LogService:
    """
    Асинхронный сервис логирования для FastAPI.
    Использует батчинг и фоновую задачу для эффективной записи в БД.
    """

    def __init__(
        self,
        batch_size: int = 50,
        flush_interval: float = 2.0,
        max_retries: int = 3,
        retry_base_delay: float = 0.5,
        retry_max_delay: float = 5.0,
    ):
        self._batch: Deque[tuple] = deque()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._lock = asyncio.Lock()
        self._last_flush = datetime.now(timezone.utc)
        self._flush_task: Optional[asyncio.Task] = None

        # Retry configuration
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._retry_max_delay = retry_max_delay

        # Failed batch storage for retry
        self._failed_batches: Deque[List[tuple]] = deque(maxlen=100)

    async def initialize(self):
        """Инициализация сервиса при старте приложения"""
        self._flush_task = asyncio.create_task(self._periodic_flush())
        logging.info("LogService initialized with batch_size=%d, flush_interval=%.1fs",
                     self._batch_size, self._flush_interval)

    async def shutdown(self):
        """Корректное завершение работы при остановке приложения"""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        await self._force_flush()
        logging.info("LogService shutdown complete")

    async def log(self, message: str, level: LogLevel):
        """Основной метод логирования"""
        context = self._get_context()

        # Немедленное логирование в stdout
        logging.log(
            self._get_logging_level(level),
            "%s (Context: %s)",
            message,
            context
        )

        # Добавляем в батч для БД
        async with self._lock:
            self._batch.append((
                message,
                level,
                context,
                datetime.now(timezone.utc)
            ))

            # Проверяем необходимость немедленного flush
            if len(self._batch) >= self._batch_size:
                await self._flush()

    async def log_info(self, message: str):
        await self.log(message, LogLevel.INFO)

    async def log_warning(self, message: str):
        await self.log(message, LogLevel.WARNING)

    async def log_error(self, message: str):
        await self.log(message, LogLevel.ERROR)

    async def log_debug(self, message: str):
        await self.log(message, LogLevel.DEBUG)

    async def _periodic_flush(self):
        """Периодическая задача для flush логов"""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)

                async with self._lock:
                    if self._batch:
                        await self._flush()

                    # Пытаемся переотправить неудачные батчи
                    if self._failed_batches:
                        await self._retry_failed_batches()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error("Error in periodic flush: %s", e)

    async def _force_flush(self):
        """Принудительный flush всех логов"""
        async with self._lock:
            if self._batch:
                await self._flush()

    async def _flush(self):
        """Сохранение батча логов в БД (вызывается под lock)"""
        if not self._batch:
            return

        # Копируем батч и очищаем
        batch_to_save = list(self._batch)
        self._batch.clear()
        self._last_flush = datetime.now(timezone.utc)

        # Сохраняем без блокировки основного потока
        success = await self._save_batch_with_retry(batch_to_save)

        if not success:
            # Сохраняем неудачный батч для последующей попытки
            self._failed_batches.append(batch_to_save)
            logging.error("Failed to save batch after %d retries, stored for later", self._max_retries)

    async def _save_batch_with_retry(self, batch: List[tuple]) -> bool:
        """Сохранение батча с retry логикой"""
        for attempt in range(self._max_retries):
            try:
                async with async_session() as session:
                    await self._save_batch(session, batch)
                return True
            except SQLAlchemyError as e:
                if attempt < self._max_retries - 1:
                    # Экспоненциальная задержка с jitter
                    delay = min(
                        self._retry_base_delay * (2 ** attempt) + secrets.randbelow(100) / 1000,
                        self._retry_max_delay
                    )
                    logging.warning(
                        "Database error on attempt %d/%d: %s. Retrying in %.2fs...",
                        attempt + 1, self._max_retries, e, delay
                    )
                    await asyncio.sleep(delay)
                else:
                    logging.error("Final attempt failed: %s", e)
            except Exception as e:
                # Неожиданная ошибка - не пытаемся повторить
                logging.error("Unexpected error saving batch: %s", e)
                return False

        return False

    async def _retry_failed_batches(self):
        """Повторная попытка отправки неудачных батчей"""
        if not self._failed_batches:
            return

        # Берем до 5 батчей для повторной отправки
        batches_to_retry = []
        for _ in range(min(5, len(self._failed_batches))):
            batches_to_retry.append(self._failed_batches.popleft())

        successfully_sent = 0
        for batch in batches_to_retry:
            if await self._save_batch_with_retry(batch):
                successfully_sent += 1
            else:
                # Возвращаем в конец очереди
                self._failed_batches.append(batch)

        if successfully_sent > 0:
            logging.info("Successfully resent %d failed batches", successfully_sent)

    async def _save_batch(self, session: AsyncSession, batch: List[tuple]):
        """Сохранение батча в БД"""
        logs = []
        for message, level, context, timestamp in batch:
            log = ApplicationLogs(
                message=message,
                level=level.value,
                context=context,
            )
            # Преобразуем timezone-aware datetime в naive для PostgreSQL
            log.creation_date = timestamp.replace(tzinfo=None)
            logs.append(log)

        session.add_all(logs)
        await session.commit()

    def _get_context(self) -> str:
        """Получение контекста вызова"""
        current_frame = inspect.currentframe()
        frames_to_skip = 3

        frame = current_frame
        for _ in range(frames_to_skip):
            if frame and frame.f_back:
                frame = frame.f_back
            else:
                return "unknown"

        if frame:
            filename = frame.f_code.co_filename
            line_number = frame.f_lineno
            function_name = frame.f_code.co_name

            # Убираем полный путь, оставляем только относительный
            if "/app/" in filename:
                filename = filename.split("/app/", 1)[1]

            return f"{filename}:{line_number} in {function_name}"

        return "unknown"

    @staticmethod
    def _get_logging_level(level: LogLevel):
        return LOGGING_LEVELS[level]


# Глобальный экземпляр сервиса
log_service = LogService()


# Функции для интеграции с FastAPI lifespan
async def setup_logging():
    """Вызывается при старте приложения"""
    # Configure root logger with custom format and colors
    logging.config.dictConfig(get_log_config())
    await log_service.initialize()


async def teardown_logging():
    """Вызывается при остановке приложения"""
    await log_service.shutdown()
