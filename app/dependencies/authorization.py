from fastapi import Header, HTTPException

from config import settings

SECRET_KEY = settings.app.secret_key


async def authorize(secret_key: str = Header(alias="Authorization")) -> None:
    if not secret_key or not secret_key.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header"
        )
