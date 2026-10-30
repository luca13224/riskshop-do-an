from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow


class SimRun(Base):
    __tablename__ = "sim_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset: Mapped[str] = mapped_column(String(10))  # dev | test
    seed: Mapped[int] = mapped_column(Integer)
    config: Mapped[dict] = mapped_column(JSON)
    rules_fingerprint: Mapped[str] = mapped_column(String(64))  # phiên bản luật đã dùng
    metrics: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)


class SimLabel(Base):
    """NHÃN THẬT của từng tài khoản mô phỏng (persona nào, có phải lạm dụng không).

    Module risk KHÔNG BAO GIỜ đọc bảng này (ERD mục 7): chỉ bộ đánh giá đọc để so với quyết định của hệ thống.
    """

    __tablename__ = "sim_labels"

    run_id: Mapped[int] = mapped_column(ForeignKey("sim_runs.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    persona: Mapped[str] = mapped_column(String(32))
    group_id: Mapped[str] = mapped_column(String(32))  # nhóm (một farm, một gia đình) để đánh giá theo nhóm
    is_abuse: Mapped[bool] = mapped_column(Boolean)
    hard_negative: Mapped[bool] = mapped_column(Boolean, default=False)
    unseen_variant: Mapped[bool] = mapped_column(Boolean, default=False)
