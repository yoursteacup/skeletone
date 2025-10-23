from fastapi import Header, HTTPException

from config import settings

SECRET_KEY = settings.app.secret_key


async def authorize(
        authorization: str = Header(alias="Authorization")
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    token = authorization.replace("Bearer ", "")
    if token != SECRET_KEY:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )

    return None
