"""Hàng đợi việc nền đơn giản, nằm ngay trong CSDL (ADR-003: không cần Celery/Redis).

- enqueue(): bên gọi thêm việc vào bảng `jobs` CÙNG transaction với hành động chính,
  nên không bao giờ có chuyện "đã lưu quyết định mà mất việc mở case" (hoặc ngược lại).
- Worker (backend/worker/main.py) lấy việc bằng SELECT ... FOR UPDATE SKIP LOCKED:
  nhiều worker chạy song song cũng không bao giờ lấy trùng một việc.
- Lỗi thì thử lại với thời gian chờ tăng dần; quá số lần thì đánh dấu failed để người xem xét.
"""

import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy import JSON, BigInteger, DateTime, Index, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base
from app.core.time import utcnow

log = logging.getLogger("jobs")

QUEUED, RUNNING, DONE, FAILED = "queued", "running", "done", "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (Index("ix_jobs_status_run_after", "status", "run_after"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(10), default=QUEUED)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    run_after: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# Đăng ký hàm xử lý theo loại việc. Worker đăng ký khi khởi động (core không import module nghiệp vụ).
HANDLERS: dict[str, Callable[[Session, dict], None]] = {}


def enqueue(db: Session, job_type: str, payload: dict) -> None:
    """Thêm việc. KHÔNG commit: việc được ghi cùng transaction của bên gọi."""
    db.add(Job(job_type=job_type, payload=payload, status=QUEUED, run_after=utcnow()))


def _claim(db: Session) -> Job | None:
    job = db.scalar(
        select(Job)
        .where(Job.status == QUEUED, Job.run_after <= utcnow())
        .order_by(Job.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if job is None:
        db.rollback()
        return None
    job.status, job.attempts, job.locked_at = RUNNING, job.attempts + 1, utcnow()
    db.commit()
    return job


def run_once(db: Session) -> bool:
    """Xử lý một việc. Trả về False nếu hàng đợi trống."""
    job = _claim(db)
    if job is None:
        return False
    try:
        HANDLERS[job.job_type](db, job.payload)
        job.status = DONE
        job.last_error = None
        db.commit()
    except Exception as exc:  # noqa: BLE001 - lỗi của một việc không được làm dừng worker
        db.rollback()
        log.exception("Job %s (%s) failed", job.id, job.job_type)
        job = db.get(Job, job.id)
        job.last_error = f"{type(exc).__name__}: {exc}"[:2000]
        if job.attempts >= job.max_attempts:
            job.status = FAILED
        else:
            job.status = QUEUED
            job.run_after = utcnow() + timedelta(seconds=2 ** job.attempts)  # chờ tăng dần: 2, 4, 8... giây
        db.commit()
    return True


def run_all(db: Session, limit: int = 1000) -> int:
    """Xử lý hết việc đang chờ (dùng trong test và script)."""
    count = 0
    while count < limit and run_once(db):
        count += 1
    return count
