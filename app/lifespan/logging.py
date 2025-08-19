from app.services.logging_service import (log_service, setup_logging,
                                          teardown_logging)
from app.utils.log_config import setup_root_logger

PRIORITY = 0


async def startup():
    try:
        setup_root_logger()
        await setup_logging()
    except Exception as e:
        await log_service.log_error("Could not start a logging lifespan")
        await log_service.log_error(str(e))


async def shutdown():
    try:
        await teardown_logging()
    except Exception as e:
        await log_service.log_error("Could not finish a logging lifespan")
        await log_service.log_error(str(e))
