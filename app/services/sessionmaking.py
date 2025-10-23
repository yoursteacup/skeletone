from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from config import settings

db_settings = settings.database
DATABASE_URL = (
    f"postgresql+asyncpg://{db_settings.username}:{db_settings.password}"
    f"@{db_settings.host}:{db_settings.port}/{db_settings.database}"
)

main_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)
log_engine = create_async_engine(DATABASE_URL, pool_size=1, max_overflow=0)

main_session = async_sessionmaker(main_engine, class_=AsyncSession, expire_on_commit=False)
log_session = async_sessionmaker(log_engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = main_session()
    try:
        yield session
    finally:
        await session.close()
