from datetime import datetime
from typing import Optional, Type, TypeVar

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (DeclarativeBase, Mapped, class_mapper,
                            mapped_column, selectinload)

ModelType = TypeVar("ModelType", bound="Base")


class Serializable:
    def to_json(self, exclude=None):
        if exclude is None:
            exclude = []

        columns = {}
        for c in class_mapper(self.__class__).columns:
            if c.key not in exclude:
                value = getattr(self, c.key)

                if isinstance(value, datetime):
                    columns[c.key] = value.isoformat()
                else:
                    columns[c.key] = value

        return columns


class Base(DeclarativeBase, Serializable):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    creation_date: Mapped[datetime] = mapped_column(insert_default=sa.func.now())
    update_date: Mapped[datetime] = mapped_column(insert_default=sa.func.now(), onupdate=sa.func.now())

    @classmethod
    async def get_single_entity(
            cls: Type[ModelType],
            session: AsyncSession,
            filter_conditions: Optional[list[sa.ColumnElement]] = None
    ) -> ModelType | None:
        stmt = (
            sa.select(cls)
            .where(*(filter_conditions or []))
            .order_by(cls.update_date.desc())
            .options(selectinload("*"))  # noqa
            .limit(1)
        )
        result = await session.execute(stmt)
        entity = result.scalar_one_or_none()
        return entity

    @classmethod
    async def get_entity_list(
            cls: Type[ModelType],
            session: AsyncSession,
            filter_conditions: Optional[list[sa.ColumnElement]] = None
    ) -> list[ModelType] | None:
        stmt = (
            sa.select(cls)
            .where(*(filter_conditions or []))
            .order_by(cls.update_date.desc())
            .options(selectinload("*"))  # noqa
        )
        result = await session.execute(stmt)
        entities = result.scalars().all()
        return list(entities) if entities else None
