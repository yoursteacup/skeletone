import json
import logging
from datetime import datetime

from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_logs import RequestLogs


async def convoy_with_logs(request: Request, call_next):
    logging.info("Request: %s %s", request.method, request.url.path)
    start_time = datetime.now()

    try:
        # Create log entry for request
        log_entry = await create_request_log(request)

        # That's where magic happens
        response = await call_next(request)

        await complete_request_log(request, response, log_entry, start_time)
        return response

    except Exception as e:
        await request.state.session.rollback()
        logging.error("Error processing request: %s", str(e))
        raise

    finally:
        await request.state.session.close()


async def create_request_log(request: Request):
    session: AsyncSession = request.state.session
    query_params = dict(request.query_params)
    headers = dict(request.headers.items())  # noqa

    try:
        body_bytes = await request.body()
        request_body = body_bytes.decode("utf-8") if body_bytes else None
    except Exception as e:
        logging.error("Error reading request body: %s", str(e))
        request_body = None

    client_ip = request.headers.get('X-Forwarded-For')
    proxy_ip = request.client.host if request.client is not None else "unknown"
    if client_ip is None:
        client_ip = proxy_ip

    log_entry = RequestLogs(
        method=request.method,
        endpoint=request.url.path,
        client_ip=client_ip,
        proxy_ip=proxy_ip,
        query_params=json.dumps(query_params),
        request_body=request_body[:1000] if request_body else None,
        headers=json.dumps(headers),
    )
    session.add(log_entry)  # noqa
    await session.commit()  # noqa
    await session.refresh(log_entry)  # noqa

    return log_entry


async def complete_request_log(request, response, log_entry, start_time):
    session = request.state.session
    process_time = (datetime.now() - start_time).total_seconds()

    response_type, response_body = determine_response_type(response)

    logging.info(
        "Response: %s for %s %s (Duration: %ss)",
        response.status_code,
        request.method,
        request.url.path,
        process_time
    )

    log_entry.status_code = response.status_code
    log_entry.response_headers = json.dumps(dict(response.headers))
    log_entry.response_type = response_type
    log_entry.response_body = response_body

    session.add(log_entry)  # noqa
    await session.commit()  # noqa


def determine_response_type(response):
    response_type = "unknown"
    response_body = None

    if isinstance(response, JSONResponse):
        response_type = "json"
        response_body = json.dumps(response.body)
    elif isinstance(response, Response) and response.media_type:
        media_type = response.media_type or "unknown"
        if response.media_type.startswith("text/"):
            response_type = "text"
            response_body = response.body.decode("utf-8")
        elif response.media_type.startswith("application/json"):
            response_type = "json"
            response_body = response.body.decode("utf-8")
        elif "octet-stream" in media_type or media_type.startswith("image/"):
            response_type = "binary"
        elif isinstance(response, StreamingResponse):
            response_type = "stream"

    return response_type, response_body
