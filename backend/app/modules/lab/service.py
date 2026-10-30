import logging
import secrets
from collections.abc import Callable

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import jobs
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.lab.models import LabRun
from app.modules.lab.scenarios import SCENARIOS, Runner
from app.modules.order import service as order_service

log = logging.getLogger("lab")
LAB_RUN_JOB = "lab_run"


def require_demo_mode() -> None:
    if not get_settings().demo_mode:
        # Ở hệ thống thật, Attack Lab coi như không tồn tại
        raise AppError("NOT_FOUND", "Not Found", 404)


def start_run(db: Session, actor: User, scenario: str) -> LabRun:
    require_demo_mode()
    if scenario not in SCENARIOS:
        raise AppError("UNKNOWN_SCENARIO", "Kịch bản không tồn tại.", 404)
    run = LabRun(scenario=scenario, status="queued", run_tag=secrets.token_hex(3), steps=[], created_by=actor.id)
    db.add(run)
    db.flush()
    jobs.enqueue(db, LAB_RUN_JOB, {"run_id": run.id})
    audit.record(db, actor_id=actor.id, action="lab.start", entity_type="lab_run", entity_id=str(run.id),
                 after={"scenario": scenario})
    db.commit()
    return run


def list_runs(db: Session, limit: int = 10) -> list[LabRun]:
    return list(db.scalars(select(LabRun).order_by(LabRun.id.desc()).limit(limit)))


def get_run(db: Session, run_id: int) -> LabRun:
    run = db.get(LabRun, run_id)
    if run is None:
        raise AppError("NOT_FOUND", "Không tìm thấy lần chạy.", 404)
    return run


def _http_client_factory(headers: dict) -> httpx.Client:
    return httpx.Client(base_url=get_settings().lab_api_base, headers=headers, timeout=15)


def execute(db: Session, payload: dict,
            client_factory: Callable[[dict], httpx.Client] = _http_client_factory, pause: float | None = None) -> None:
    """Hàm xử lý việc nền "lab_run" (worker gọi). Cập nhật từng bước vào lab_runs để giao diện theo dõi."""
    run = db.get(LabRun, payload["run_id"])
    if run is None or run.status != "queued":
        return
    actor = db.get(User, run.created_by)
    run.status = "running"
    db.commit()

    def record_step(step: dict) -> None:
        run.steps = [*run.steps, step]  # gán list mới để SQLAlchemy nhận ra cột JSON đã đổi
        db.commit()

    def ship(order_code: str, status: str) -> None:
        order_service.update_shipment(db, actor, order_code, status, "Attack Lab giả lập vận chuyển")

    kwargs = {} if pause is None else {"pause": pause}
    runner = Runner(client_factory, record_step, ship, run.run_tag, **kwargs)
    try:
        run.summary = SCENARIOS[run.scenario].run(runner)
        run.status, run.passed = "done", runner.all_ok
    except Exception as exc:  # noqa: BLE001 - lỗi kịch bản không được làm sập worker
        log.exception("Lab run %s failed", run.id)
        db.rollback()
        run = db.get(LabRun, payload["run_id"])
        run.status, run.passed, run.summary = "failed", False, f"Lỗi khi chạy: {type(exc).__name__}: {exc}"[:500]
    run.finished_at = utcnow()
    db.commit()
