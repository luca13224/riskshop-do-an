"""Bảng của module appeals: khiếu nại của khách về một quyết định rủi ro (ADR-006)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

OPEN = "OPEN"
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"


class Appeal(Base):
    __tablename__ = "appeals"
    __table_args__ = (Index("ix_appeals_status_created", "status", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appeal_code: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("risk_decisions.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    policy: Mapped[str] = mapped_column(String(10))  # voucher | cod
    message: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(10), default=OPEN)
    response: Mapped[str | None] = mapped_column(String(1000))  # trả lời hiển thị cho khách
    handled_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    # "user_id:policy" khi đang mở, NULL khi đã kết luận. UNIQUE -> mỗi khách chỉ có MỘT khiếu nại đang mở
    # cho mỗi chính sách, kể cả khi hai request gửi cùng lúc (cùng kỹ thuật với open_cluster_key của case).
    open_key: Mapped[str | None] = mapped_column(String(40), unique=True)
