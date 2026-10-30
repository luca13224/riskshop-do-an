from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow


class LabRun(Base):
    """Một lần chạy kịch bản. `steps` được cập nhật dần trong lúc chạy để giao diện theo dõi."""

    __tablename__ = "lab_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scenario: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(10), default="queued")  # queued | running | done | failed
    run_tag: Mapped[str] = mapped_column(String(16))  # gắn vào email/thiết bị để phân biệt các lần chạy
    steps: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(String(500))
    passed: Mapped[bool | None] = mapped_column()  # kết quả thực tế có khớp kỳ vọng không
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
