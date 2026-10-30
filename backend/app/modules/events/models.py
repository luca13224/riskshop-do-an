from datetime import datetime

from sqlalchemy import JSON, BigInteger, CHAR, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Loại sự kiện
SIGNUP = "signup"
LOGIN = "login"
PRODUCT_VIEW = "product_view"
VOUCHER_ATTEMPT = "voucher_attempt"


class Event(Base):
    """Một hành vi của người dùng. Bảng chỉ ghi thêm, không sửa, không xóa."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_device_type_time", "device_id", "event_type", "occurred_at"),
        Index("ix_events_user_type_time", "user_id", "event_type", "occurred_at"),
        Index("ix_events_time", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(32))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"))
    ip_hash: Mapped[str | None] = mapped_column(CHAR(64))
    payload: Mapped[dict | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
