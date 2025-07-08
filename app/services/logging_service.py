import inspect
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.application_logs import ApplicationLogs
from app.services.sessionmaking import get_session
from app.utils.enums import LogLevel

LOGGING_LEVELS = {
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.DEBUG: logging.DEBUG,
}


class LogService:
    def __init__(self):
        self._session_pool: Optional[AsyncSession] = None

    async def log(self, message: str, level: LogLevel):
        current_frame = inspect.currentframe()
        if (
                current_frame is None or
                current_frame.f_back is None or
                current_frame.f_back.f_back is None
        ):
            context = "unknown"
        else:
            frame = current_frame.f_back.f_back
            filename = frame.f_code.co_filename
            line_number = frame.f_lineno
            function_name = frame.f_code.co_name
            context = f"{filename}:{line_number} in {function_name}"

        logging.log(
            self._get_logging_level(level),
            "%s: %s (Context: %s)",
            level.name,
            message,
            context
        )

        # Use pooled session or create new one
        if self._session_pool is None:
            async for session in get_session():
                try:
                    new_log = ApplicationLogs(
                        message=message,
                        level=level.value,
                        context=context,
                    )
                    session.add(new_log)
                    await session.commit()
                except Exception as e:
                    logging.error(f"Failed to log to database: {e}")
                    await session.rollback()
        else:
            try:
                new_log = ApplicationLogs(
                    message=message,
                    level=level.value,
                    context=context,
                )
                self._session_pool.add(new_log)
                await self._session_pool.commit()
            except Exception as e:
                logging.error(f"Failed to log to database: {e}")
                await self._session_pool.rollback()

    async def log_info(self, message: str):
        await self.log(message, LogLevel.INFO)

    async def log_warning(self, message: str):
        await self.log(message, LogLevel.WARNING)

    async def log_error(self, message: str):
        await self.log(message, LogLevel.ERROR)

    async def log_debug(self, message: str):
        await self.log(message, LogLevel.DEBUG)

    @staticmethod
    def _get_logging_level(level: LogLevel):
        return LOGGING_LEVELS[level]


# Modular singleton - single instance for the entire application
log_service = LogService()
