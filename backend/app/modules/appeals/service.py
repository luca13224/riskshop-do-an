"""Logic khiếu nại (ADR-006).

Luồng: khách bị hạn chế -> gửi khiếu nại cho MỘT quyết định cụ thể -> Risk Manager/Admin xem xét
-> chấp nhận (miễn trừ chính sách đó 30 ngày, duyệt đơn đang giữ) hoặc từ chối, kèm câu trả lời cho khách.
"""

import secrets
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.appeals import models as m
from app.modules.appeals.schemas import AppealOut, EligibleOut, StaffAppealDetailOut, StaffAppealOut
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.order import service as order_service
from app.modules.risk import service as risk
from app.modules.risk.models import RiskDecision

APPEAL_WINDOW_DAYS = 30  # chỉ khiếu nại được các quyết định trong 30 ngày gần nhất
EXEMPT_DAYS = 30  # chấp nhận khiếu nại -> miễn trừ chính sách đó 30 ngày

# Câu chữ cho khách: nói KẾT QUẢ, không nói luật nào đã khớp
_LABELS = {
    ("voucher", None): "Mã giảm giá không được áp dụng",
    ("cod", "hold_order"): "Đơn hàng bị giữ lại chờ xác minh",
    ("cod", "block"): "Đơn hàng không được chấp nhận",
    ("cod", "disable_cod"): "Không được chọn thanh toán khi nhận hàng (COD)",
}


def _policies(actions: dict) -> list[tuple[str, str | None]]:
    """Một quyết định có thể hạn chế cả voucher lẫn COD; mỗi chính sách là một mục khiếu nại riêng."""
    out: list[tuple[str, str | None]] = []
    if actions.get("remove_voucher"):
        out.append(("voucher", None))
    for key in ("block", "hold_order", "disable_cod"):  # lấy hành động COD nặng nhất
        if actions.get(key):
            out.append(("cod", key))
            break
    return out


def _label(policy: str, actions: dict) -> str:
    if policy == "cod" and actions.get("restrict_account"):
        return "Tài khoản tạm thời chưa thể đặt hàng"
    for p, key in _policies(actions):
        if p == policy:
            return _LABELS[(p, key)]
    return "Quyết định hạn chế"


def _new_code() -> str:
    return f"AP{utcnow():%y%m%d}{secrets.token_hex(3).upper()}"


# ---------- Phía khách hàng ----------

def eligible(db: Session, user: User) -> list[EligibleOut]:
    since = utcnow() - timedelta(days=APPEAL_WINDOW_DAYS)
    appealed = set(db.execute(
        select(m.Appeal.decision_id, m.Appeal.policy).where(m.Appeal.user_id == user.id)
    ).all())
    open_by_policy = dict(db.execute(
        select(m.Appeal.policy, m.Appeal.appeal_code).where(m.Appeal.user_id == user.id, m.Appeal.status == m.OPEN)
    ).all())

    # Mỗi lần thử áp voucher đều sinh một quyết định: chỉ giữ lần MỚI NHẤT theo (chính sách, đơn hàng)
    seen: set[tuple[str, int | None]] = set()
    items: list[EligibleOut] = []
    for d in risk.restrictive_decisions_for_user(db, user.id, since):
        for policy, _ in _policies(d.actions):
            key = (policy, d.order_id)
            if key in seen or (d.id, policy) in appealed:
                continue
            seen.add(key)
            brief = order_service.order_brief(db, d.order_id) if d.order_id else None
            items.append(EligibleOut(
                decision_id=d.public_id, policy=policy, label=_label(policy, d.actions), context=d.context,
                created_at=d.created_at, order_code=brief["order_code"] if brief else None,
                order_status=brief["status"] if brief else None, open_appeal=open_by_policy.get(policy),
            ))
    return items[:10]


def create(db: Session, user: User, decision_public_id: str, policy: str, message: str) -> AppealOut:
    d = risk.decision_by_public_id(db, decision_public_id)
    # Không phải quyết định của mình thì báo "không tìm thấy" (không cho dò quyết định của người khác)
    if d is None or d.user_id != user.id:
        raise AppError("DECISION_NOT_FOUND", "Không tìm thấy lần bị hạn chế này.", 404)
    if policy not in [p for p, _ in _policies(d.actions)]:
        raise AppError("NOT_RESTRICTED", "Quyết định này không hạn chế mục bạn chọn.", 422)
    if d.created_at < utcnow() - timedelta(days=APPEAL_WINDOW_DAYS):
        raise AppError("APPEAL_EXPIRED", f"Chỉ khiếu nại được trong {APPEAL_WINDOW_DAYS} ngày.", 422)
    if db.scalar(select(m.Appeal.id).where(m.Appeal.decision_id == d.id, m.Appeal.policy == policy)):
        raise AppError("ALREADY_APPEALED", "Bạn đã khiếu nại lần này rồi.", 409)

    appeal = m.Appeal(appeal_code=_new_code(), user_id=user.id, decision_id=d.id, order_id=d.order_id,
                      policy=policy, message=message, open_key=f"{user.id}:{policy}")
    db.add(appeal)
    try:
        db.commit()
    except IntegrityError as exc:  # open_key UNIQUE: đã có khiếu nại đang mở cho chính sách này
        db.rollback()
        raise AppError("APPEAL_ALREADY_OPEN",
                       "Bạn đang có một khiếu nại chưa được xử lý cho mục này. Vui lòng chờ kết quả.", 409) from exc
    return _to_out(db, appeal)


def list_mine(db: Session, user: User) -> list[AppealOut]:
    rows = db.scalars(select(m.Appeal).where(m.Appeal.user_id == user.id).order_by(m.Appeal.id.desc()))
    return [_to_out(db, a) for a in rows]


def _to_out(db: Session, a: m.Appeal) -> AppealOut:
    d = risk.decision_info(db, a.decision_id)
    brief = order_service.order_brief(db, a.order_id) if a.order_id else None
    return AppealOut(
        appeal_code=a.appeal_code, policy=a.policy, label=_label(a.policy, d.actions if d else {}),
        status=a.status, message=a.message, response=a.response,
        order_code=brief["order_code"] if brief else None, created_at=a.created_at, resolved_at=a.resolved_at,
    )


# ---------- Phía nhân viên ----------

def _staff_out(db: Session, a: m.Appeal, users: dict[int, User]) -> StaffAppealOut:
    base = _to_out(db, a).model_dump()
    owner = users[a.user_id]
    handler = users.get(a.handled_by) if a.handled_by else None
    return StaffAppealOut(**base, user_id=owner.id, user_email=owner.email, user_name=owner.full_name,
                          handled_by_name=handler.full_name if handler else None)


def _users(db: Session, appeals: list[m.Appeal]) -> dict[int, User]:
    ids = {a.user_id for a in appeals} | {a.handled_by for a in appeals if a.handled_by}
    return {u.id: u for u in db.scalars(select(User).where(User.id.in_(ids)))} if ids else {}


def list_appeals(db: Session, status: str | None, limit: int = 100) -> list[StaffAppealOut]:
    q = select(m.Appeal).order_by(m.Appeal.id.desc()).limit(limit)
    if status:
        q = q.where(m.Appeal.status == status)
    appeals = list(db.scalars(q))
    users = _users(db, appeals)
    return [_staff_out(db, a, users) for a in appeals]


def _get(db: Session, code: str, lock: bool = False) -> m.Appeal:
    q = select(m.Appeal).where(m.Appeal.appeal_code == code)
    appeal = db.scalar(q.with_for_update() if lock else q)
    if appeal is None:
        raise AppError("APPEAL_NOT_FOUND", "Không tìm thấy khiếu nại.", 404)
    return appeal


def get_appeal(db: Session, code: str) -> StaffAppealDetailOut:
    a = _get(db, code)
    base = _staff_out(db, a, _users(db, [a])).model_dump()
    decisions = risk.decisions_by_ids(db, [a.decision_id])
    others = db.scalar(select(func.count()).where(m.Appeal.user_id == a.user_id, m.Appeal.id != a.id))
    return StaffAppealDetailOut(
        **base, decision=decisions[0] if decisions else None,
        active_exemptions=sorted(risk.active_exemptions(db, a.user_id)), other_appeals=others,
    )


def resolve(db: Session, staff: User, code: str, outcome: str, response: str) -> StaffAppealDetailOut:
    a = _get(db, code, lock=True)
    if a.status != m.OPEN:
        raise AppError("APPEAL_CLOSED", "Khiếu nại này đã được kết luận.", 409)
    a.status, a.response, a.handled_by, a.resolved_at = outcome, response, staff.id, utcnow()
    a.open_key = None  # khách có thể gửi khiếu nại mới cho chính sách này
    order_status = None
    if outcome == m.ACCEPTED:
        risk.grant_exemption(db, user_id=a.user_id, policy=a.policy, days=EXEMPT_DAYS,
                             reason=f"Chấp nhận khiếu nại {a.appeal_code}", actor_id=staff.id,
                             source_ref=a.appeal_code)
        # Quyết định khóa quyền mua hàng (ADR-010): chấp nhận khiếu nại thì gỡ khóa luôn
        d = db.get(RiskDecision, a.decision_id)
        if d is not None and (d.actions or {}).get("restrict_account"):
            risk.lift_restrictions(db, a.user_id, staff.id, f"Chấp nhận khiếu nại {a.appeal_code}")
        if a.order_id:  # đơn đang bị giữ chờ duyệt thì duyệt luôn (đơn ở trạng thái khác: không đổi)
            order_status = order_service.resolve_review(
                db, a.order_id, approve=True, actor_id=staff.id, note=f"Chấp nhận khiếu nại {a.appeal_code}"
            )
    audit.record(db, actor_id=staff.id, action="appeal.resolve", entity_type="appeal", entity_id=a.appeal_code,
                 before={"status": m.OPEN},
                 after={"status": outcome, "exempt_policy": a.policy if outcome == m.ACCEPTED else None,
                        "exempt_days": EXEMPT_DAYS if outcome == m.ACCEPTED else None,
                        "order_status": order_status},
                 note=response)
    db.commit()
    return get_appeal(db, code)


def open_count(db: Session) -> int:
    """Hàm công khai cho dashboard."""
    return db.scalar(select(func.count()).where(m.Appeal.status == m.OPEN)) or 0
