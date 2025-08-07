from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import logging_middleware
from app.routers import get_all_routers
from app.services.logging_service import setup_logging, teardown_logging
from app.services.sessionmaking import async_session
from config import settings


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    await setup_logging()
    yield
    await teardown_logging()


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

    uvicorn.run(app, host="0.0.0.0", port=settings.app.port)  # nosec B104 - safe inside docker behind nginx
