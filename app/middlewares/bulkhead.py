import asyncio

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class BulkheadMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_concurrent_requests: int = 40, timeout: float = 0):
        super().__init__(app)
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.timeout = timeout

    async def dispatch(self, request, call_next):
        try:
            if self.timeout > 0:
                async with asyncio.wait_for(self.semaphore.acquire(), timeout=self.timeout):
                    try:
                        response = await call_next(request)
                        return response
                    finally:
                        self.semaphore.release()
            else:
                async with self.semaphore:
                    response = await call_next(request)
                    return response

        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=420,
                content={"detail": "Too many concurrent requests"}
            )
