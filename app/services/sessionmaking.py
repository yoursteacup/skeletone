from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from config import settings

db_settings = settings.database
DATABASE_URL = (
    f"postgresql+asyncpg://{db_settings.username}:{db_settings.password}"
    f"@{db_settings.host}:{db_settings.port}/{db_settings.database}"
)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
