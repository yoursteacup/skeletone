from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import logging_middleware
from app.lifespan import get_all_shutdown_tasks, get_all_startup_tasks
from app.routers import get_all_routers
from app.services.sessionmaking import async_session
from app.utils.uvicorn_log_config import log_config
from config import settings


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Run all startup tasks
    for startup_task in get_all_startup_tasks():
        await startup_task()

    yield

    # Run all shutdown tasks
    for shutdown_task in get_all_shutdown_tasks():
        await shutdown_task()


app = FastAPI(lifespan=lifespan)
origins = settings.app.allowed_origins
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins or [],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

for router in get_all_routers():
    app.include_router(router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    session = async_session()
    request.state.session = session
    return await logging_middleware.convoy_with_logs(request, call_next)


if __name__ == "__main__":
    import uvicorn  # noqa

    uvicorn.run(
        app,
        host="0.0.0.0",  # nosec B104 - safe inside docker behind nginx
        port=settings.app.port,
        log_config=log_config
    )
