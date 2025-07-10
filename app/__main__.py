from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import logging_middleware
from app.services.sessionmaking import get_session
from config import settings

app = FastAPI()
origins = settings.app.allowed_origins
app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=origins or [],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    async for session in get_session():  # noqa
        request.state.session = session
        return await logging_middleware.convoy_with_logs(request, call_next)


if __name__ == "__main__":
    import uvicorn  # noqa

    uvicorn.run(app, host="0.0.0.0", port=settings.app.port)  # nosec B104 - safe inside docker behind nginx
