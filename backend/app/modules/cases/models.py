from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

OPEN = "OPEN"
IN_REVIEW = "IN_REVIEW"
CONFIRMED_ABUSE = "CONFIRMED_ABUSE"
CLEARED = "CLEARED"
CLOSED_STATUSES = (CONFIRMED_ABUSE, CLEARED)


class RiskCase(Base):
    __tablename__ = "risk_cases"
    __table_args__ = (Index("ix_risk_cases_status_opened", "status", "opened_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_code: Mapped[str] = mapped_column(String(20), unique=True)
    policy: Mapped[str] = mapped_column(String(10))  # voucher | cod
    status: Mapped[str] = mapped_column(String(20), default=OPEN)
    cluster_key: Mapped[str] = mapped_column(String(64))  # vd "device:42", "order:7"
    # = cluster_key khi case đang mở, NULL khi đã đóng. UNIQUE cho phép nhiều NULL,
    # nên mỗi cụm chỉ có tối đa MỘT case đang mở (MariaDB không có partial unique index).
    open_cluster_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    primary_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    outcome_reason: Mapped[str | None] = mapped_column(String(1000))
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)


class CaseDecision(Base):
    """Các quyết định rủi ro thuộc một case (một case cụm có thể gom nhiều quyết định)."""

    __tablename__ = "case_decisions"

    case_id: Mapped[int] = mapped_column(ForeignKey("risk_cases.id"), primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("risk_decisions.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CaseAction(Base):
    """Lịch sử xử lý case (chỉ ghi thêm)."""

    __tablename__ = "case_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("risk_cases.id"), index=True)
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # None = hệ thống
    action: Mapped[str] = mapped_column(String(32))
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(1000), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
