from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RequestLogs(Base):
    __tablename__ = "request_logs"

    method: Mapped[str] = mapped_column()
    endpoint: Mapped[str] = mapped_column()
    status_code: Mapped[int] = mapped_column(nullable=True)
    client_ip: Mapped[str] = mapped_column(nullable=True)
    proxy_ip: Mapped[str] = mapped_column(nullable=True)
    query_params: Mapped[str] = mapped_column(nullable=True)
    request_body: Mapped[str] = mapped_column(nullable=True)
    headers: Mapped[str] = mapped_column(nullable=True)
    response_headers: Mapped[str] = mapped_column(nullable=True)
    response_body: Mapped[str] = mapped_column(nullable=True)
    response_type: Mapped[str] = mapped_column(nullable=True)

    update_date = None  # type: ignore
