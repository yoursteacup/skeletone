from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.enums import LogLevel


class ApplicationLogs(Base):
    __tablename__ = "application_logs"

    message: Mapped[str] = mapped_column()
    level: Mapped[LogLevel] = mapped_column()
    context: Mapped[str] = mapped_column()

    update_date = None  # type: ignore
