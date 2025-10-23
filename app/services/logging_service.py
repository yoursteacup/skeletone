import asyncio
import inspect
import logging
import uuid
from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_logs import ApplicationLogs
from app.models.request_logs import RequestLogs
from app.services.sessionmaking import log_session
from app.utils.enums import LogLevel


class LogService:
    def __init__(
            self,
            flush_interval: float = 3.0,
            batch_size: int = 20,
            retry_limit: int = 5,
            retry_base_delay: float = 1.0,
            write_to_stdout: bool = True,
            with_context: bool = True,
            fallback_file: str = "failed_logs.txt"
    ):
        # Settings
        self._request_map: dict = {}
        self.flush_interval = flush_interval
        self.batch_size = batch_size
        self.retry_limit = retry_limit
        self.retry_base_delay = retry_base_delay
        self.write_to_stdout = write_to_stdout
        self.with_context = with_context
        self.fallback_file = fallback_file

        # Queues
        self._queue: deque = deque()
        self._failed_batches: deque = deque(maxlen=100)

        # Metrics
        self.logs_written = 0
        self.batches_failed = 0
        self.batches_retried = 0

        # Async infra
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        self._logger = logging.getLogger("LogService")
        self._logger.setLevel(logging.INFO)

    async def startup(self) -> None:
        self._stop_event.clear()
        self._task = asyncio.create_task(self._periodic_flush())
        self._logger.info("LogService started")

    async def shutdown(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self._force_flush()
        self._logger.info("LogService stopped")

    def log_request(self, request_data: dict) -> str:
        correlation_id = uuid.uuid4().hex[:8]
        request_data["correlation_id"] = correlation_id
        self._queue.append(("request_insert", request_data))

        return correlation_id

    def conclude_log_request(self, request_data: dict, correlation_id: str) -> None:
        self._queue.append(("request_update", {**request_data, "correlation_id": correlation_id}))

    def log(
            self,
            level: str,
            message: str,
            context: Optional[str] = None,
    ) -> None:
        if self.with_context and not context:
            context = self._get_context()

        record = ("app", {
            "creation_date": datetime.now(),
            "level": level,
            "message": message,
            "context": context,
        })
        self._queue.append(record)

        if self.write_to_stdout:
            self._logger.info(
                "[%s] %s%s",
                level,
                message,
                f" ({context})" if context else ''
            )

    def log_info(self, message: str):
        self.log(LogLevel.INFO.value, message)

    def log_warning(self, message: str):
        self.log(LogLevel.WARNING.value, message)

    def log_error(self, message: str):
        self.log(LogLevel.ERROR.value, message)

    def log_debug(self, message: str):
        self.log(LogLevel.DEBUG.value, message)

    async def _periodic_flush(self) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(self.flush_interval)
            await self._flush_once()

    async def _flush_once(self) -> None:
        if not self._queue and not self._failed_batches:
            return

        batch = [self._queue.popleft() for _ in range(min(len(self._queue), self.batch_size))]
        if batch:
            await self._write_with_retry(batch)

    async def _write_with_retry(
            self,
            batch: List[Tuple[str, dict]],
            retrying: bool = False
    ) -> None:
        for attempt in range(self.retry_limit):
            try:
                async with log_session() as session:
                    await self._write_batch(session, batch)
                self.logs_written += len(batch)
                if retrying:
                    self.batches_retried += 1
                return
            except Exception:
                delay = self.retry_base_delay * (2**attempt) + (0.1 * attempt)
                await asyncio.sleep(delay)

        self.batches_failed += 1
        self._failed_batches.append(batch)
        await self._fallback_to_file(batch)

    async def _write_batch(
            self,
            session: AsyncSession,
            batch: List[Tuple[str, dict]]
    ) -> None:
        for kind, data in batch:
            if kind == "app":
                await session.execute(insert(ApplicationLogs).values(**data))
            elif kind == "request_insert":
                correlation_id = data["correlation_id"]
                del data["correlation_id"]
                res = await session.execute(
                    insert(RequestLogs).values(**data).returning(RequestLogs.id)
                )
                request_id = res.scalar()
                self._request_map[correlation_id] = request_id
            elif kind == "request_update":
                request_id = self._request_map.get(data["correlation_id"])
                del data["correlation_id"]
                if request_id:
                    await session.execute(
                        update(RequestLogs)
                        .where(RequestLogs.id == request_id)
                        .values(**data)
                    )

            await session.commit()

    @staticmethod
    def _get_context() -> str:
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

    async def _force_flush(self) -> None:
        while self._queue:
            batch = [self._queue.popleft() for _ in range(min(len(self._queue), self.batch_size))]
            try:
                async with log_session() as session:
                    await self._write_batch(session, batch)
            except Exception:
                await self._fallback_to_file(batch)

    async def _fallback_to_file(self, batch: List[Tuple[str, dict]]) -> None:
        try:
            with open(self.fallback_file, "a", encoding="utf-8") as f:
                for row in batch:
                    f.write(
                        f"{row[1]['creation_date']} [{row[1]['level']}]"
                        f" {row[1]['message']} {row[1].get('context', '')}\n"
                    )
        except Exception:
            pass  # nosec B110 - Fallback must not fail


log_service = LogService()
