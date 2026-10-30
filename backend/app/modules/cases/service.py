"""Quản lý case: mở/gom case từ quyết định rủi ro (worker gọi), nhận xử lý, kết luận.

Vòng đời (docs/REQUIREMENTS, ERD mục 5.6 bản tư vấn):
    OPEN --nhận xử lý--> IN_REVIEW --kết luận--> CONFIRMED_ABUSE | CLEARED
Case COD gắn với một đơn đang chờ xác minh: kết luận "không vi phạm" thì duyệt đơn,
"xác nhận lạm dụng" thì từ chối đơn và hoàn hàng về kho.
Mỗi thao tác của nhân viên đều ghi case_actions và audit_logs trong cùng transaction.
"""

import secrets
import string

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.audit import service as audit
from app.modules.auth import service as auth_service
from app.modules.auth.models import User
from app.modules.cases import models as m
from app.modules.cases.schemas import CaseActionOut, CaseDetailOut, CaseSummaryOut
from app.modules.order import service as order_service
from app.modules.risk import service as risk


def _new_code() -> str:
    return "CS" + utcnow().strftime("%y%m%d") + "".join(secrets.choice(string.ascii_uppercase + string.digits)
                                                         for _ in range(5))


def _cluster_for(decision) -> tuple[str, str]:
    """(chính sách, khóa cụm) của một quyết định.

    - Đơn COD bị giữ/chặn: mỗi đơn một case ("order:<id>").
    - Lạm dụng voucher: gom theo THIẾT BỊ ("device:<id>"), để cả cụm tài khoản farm nằm chung một case.
    """
    actions = decision.actions or {}
    if actions.get("hold_order") or actions.get("block"):
        key = f"order:{decision.order_id}" if decision.order_id else f"user:{decision.user_id}"
        return "cod", key
    device_id = (decision.features_snapshot or {}).get("device_id")
    return "voucher", f"device:{device_id}" if device_id else f"user:{decision.user_id}"


def open_from_decision(db: Session, payload: dict) -> None:
    """Xử lý việc nền "open_case": mở case mới hoặc gom vào case đang mở của cùng cụm."""
    decision = risk.decision_info(db, payload["decision_id"])
    if decision is None:
        return
    policy, key = _cluster_for(decision)
    case = db.scalar(select(m.RiskCase).where(m.RiskCase.open_cluster_key == key))
    if case is None:
        case = m.RiskCase(case_code=_new_code(), policy=policy, status=m.OPEN, cluster_key=key,
                          open_cluster_key=key, primary_user_id=decision.user_id, order_id=decision.order_id)
        db.add(case)
        try:
            db.flush()
        except IntegrityError:
            # Hai worker cùng mở case cho một cụm: bên thua dùng case của bên thắng
            db.rollback()
            case = db.scalar(select(m.RiskCase).where(m.RiskCase.open_cluster_key == key))
        else:
            db.add(m.CaseAction(case_id=case.id, staff_id=None, action="open", from_status=None,
                                to_status=m.OPEN, note="Hệ thống tự mở case từ quyết định rủi ro"))
    db.execute(
        mysql_insert(m.CaseDecision).values(case_id=case.id, decision_id=decision.id, added_at=utcnow())
        .prefix_with("IGNORE")  # việc chạy lại (retry) không tạo bản ghi trùng
    )


# ---------- Đọc ----------

def _cluster_label(key: str) -> str:
    kind, _, value = key.partition(":")
    return {"device": "Cụm theo thiết bị #", "order": "Đơn hàng #", "user": "Tài khoản #"}.get(kind, "") + value


def _summaries(db: Session, cases: list[m.RiskCase]) -> list[CaseSummaryOut]:
    ids = [c.id for c in cases]
    stats = {}
    if ids:
        stats = {
            row.case_id: (row.n, row.max_score)
            for row in db.execute(
                select(m.CaseDecision.case_id, func.count().label("n"),
                       func.max(risk.RiskDecision.score).label("max_score"))
                .join(risk.RiskDecision, risk.RiskDecision.id == m.CaseDecision.decision_id)
                .where(m.CaseDecision.case_id.in_(ids))
                .group_by(m.CaseDecision.case_id)
            )
        }
    users = {u.id: u for u in db.scalars(
        select(User).where(User.id.in_({c.primary_user_id for c in cases} | {c.assigned_to for c in cases if c.assigned_to}))
    )} if cases else {}
    return [
        CaseSummaryOut(
            case_code=c.case_code,
            policy=c.policy,
            status=c.status,
            cluster_label=_cluster_label(c.cluster_key),
            primary_user_email=users[c.primary_user_id].email,
            decision_count=stats.get(c.id, (0, 0))[0],
            max_score=stats.get(c.id, (0, 0))[1] or 0,
            assigned_to_name=users[c.assigned_to].full_name if c.assigned_to else None,
            opened_at=c.opened_at,
            closed_at=c.closed_at,
        )
        for c in cases
    ]


def list_cases(db: Session, status: str | None, limit: int = 100) -> list[CaseSummaryOut]:
    query = select(m.RiskCase)
    if status == "ACTIVE":
        query = query.where(m.RiskCase.status.in_([m.OPEN, m.IN_REVIEW]))
    elif status == "CLOSED":
        query = query.where(m.RiskCase.status.in_(m.CLOSED_STATUSES))
    cases = db.scalars(query.order_by(m.RiskCase.id.desc()).limit(limit)).all()
    return _summaries(db, list(cases))


def _get(db: Session, code: str, lock: bool = False) -> m.RiskCase:
    query = select(m.RiskCase).where(m.RiskCase.case_code == code)
    case = db.scalar(query.with_for_update() if lock else query)
    if case is None:
        raise AppError("CASE_NOT_FOUND", "Không tìm thấy case.", 404)
    return case


def get_case(db: Session, code: str) -> CaseDetailOut:
    case = _get(db, code)
    decision_ids = list(db.scalars(select(m.CaseDecision.decision_id).where(m.CaseDecision.case_id == case.id)))
    linked = []
    kind, _, value = case.cluster_key.partition(":")
    if kind == "device":
        linked = auth_service.accounts_on_device(db, int(value))
    actions = db.execute(
        select(m.CaseAction, User.full_name)
        .outerjoin(User, User.id == m.CaseAction.staff_id)
        .where(m.CaseAction.case_id == case.id)
        .order_by(m.CaseAction.id)
    ).all()
    summary = _summaries(db, [case])[0]
    return CaseDetailOut(
        **summary.model_dump(),
        outcome_reason=case.outcome_reason,
        linked_accounts=linked,
        decisions=risk.decisions_by_ids(db, decision_ids),
        actions=[
            CaseActionOut(action=a.action, from_status=a.from_status, to_status=a.to_status, note=a.note,
                          staff_name=name, created_at=a.created_at)
            for a, name in actions
        ],
        order=order_service.order_brief(db, case.order_id) if case.order_id else None,
    )


# ---------- Thao tác của nhân viên ----------

def claim(db: Session, staff: User, code: str) -> CaseDetailOut:
    case = _get(db, code, lock=True)
    if case.status != m.OPEN:
        raise AppError("INVALID_TRANSITION", "Case này không ở trạng thái chờ nhận.", 409)
    case.status, case.assigned_to = m.IN_REVIEW, staff.id
    db.add(m.CaseAction(case_id=case.id, staff_id=staff.id, action="claim", from_status=m.OPEN,
                        to_status=m.IN_REVIEW, note=""))
    audit.record(db, actor_id=staff.id, action="case.claim", entity_type="case", entity_id=case.case_code,
                 before={"status": m.OPEN}, after={"status": m.IN_REVIEW, "assigned_to": staff.id})
    db.commit()
    return get_case(db, code)


def resolve(db: Session, staff: User, code: str, outcome: str, note: str) -> CaseDetailOut:
    case = _get(db, code, lock=True)
    if case.status != m.IN_REVIEW:
        raise AppError("INVALID_TRANSITION", "Cần nhận xử lý case trước khi kết luận.", 409)
    if case.assigned_to != staff.id:
        raise AppError("NOT_ASSIGNEE", "Case đang do người khác xử lý.", 403)
    before = {"status": case.status}
    case.status, case.outcome_reason, case.closed_at = outcome, note, utcnow()
    case.open_cluster_key = None  # đóng case: cụm này có thể mở case mới nếu tái phạm
    order_status = None
    if case.order_id:
        # Case COD: kết luận của nhân viên quyết định số phận đơn đang chờ xác minh
        order_status = order_service.resolve_review(
            db, case.order_id, approve=(outcome == m.CLEARED), actor_id=staff.id,
            note=f"Kết luận case {case.case_code}",
        )
    db.add(m.CaseAction(case_id=case.id, staff_id=staff.id, action="resolve", from_status=m.IN_REVIEW,
                        to_status=outcome, note=note))
    audit.record(db, actor_id=staff.id, action="case.resolve", entity_type="case", entity_id=case.case_code,
                 before=before, after={"status": outcome, "order_status": order_status}, note=note)
    db.commit()
    return get_case(db, code)
