from app.services.logging_service import log_service
from app.utils.log_config import setup_root_logger

PRIORITY = 0


async def startup():
    setup_root_logger()
    await log_service.startup()


async def shutdown():
    await log_service.shutdown()
