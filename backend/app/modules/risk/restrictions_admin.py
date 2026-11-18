"""Danh sách tài khoản bị hạn chế quyền mua hàng cho Console (chỉ đọc).

Một nơi xem mọi lệnh khóa (ADR-010, 011, 015): ai bị khóa, loại gì, vì sao, do hệ thống hay nhân viên,
đến khi nào, ai gỡ và vì sao. Trạng thái tính lúc đọc:
- active: chưa gỡ và (vô thời hạn hoặc chưa hết hạn)
- expired: chưa gỡ nhưng đã quá `expires_at` (tự hết hiệu lực, không cần ai làm gì)
- lifted: nhân viên đã gỡ (ghi `lifted_at`, `lifted_by`, `lift_reason`)
Gỡ khóa vẫn đi qua `service.lift_restrictions` (Risk Manager / Admin, bắt buộc lý do, có audit).
"""

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.core.search import LIKE_ESCAPE, contains_pattern
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.cases.models import RiskCase
from app.modules.risk.models import AccountRestriction
from app.modules.risk.service import latest_trust

STATUSES = ("active", "expired", "lifted")


def _status_expr(now):
    R = AccountRestriction
    return case(
        (R.lifted_at.is_not(None), "lifted"),
        (and_(R.expires_at.is_not(None), R.expires_at <= now), "expired"),
        else_="active",
    )


def list_restrictions(db: Session, *, status: str | None = "active", kind: str | None = None, q: str | None = None,
                      page: int = 1, page_size: int = 20) -> dict:
    R = AccountRestriction
    now = utcnow()
    status_col = _status_expr(now)
    lifter = aliased(User)
    conditions = []
    if kind:
        conditions.append(R.kind == kind)
    if q:
        pattern = contains_pattern(q)
        conditions.append(or_(User.email.like(pattern, escape=LIKE_ESCAPE), User.full_name.like(pattern, escape=LIKE_ESCAPE)))

    # Đếm theo trạng thái TRƯỚC khi áp bộ lọc trạng thái, để chip nào cũng hiện đúng con số của nó
    counts = dict(db.execute(
        select(status_col, func.count()).join(User, User.id == R.user_id).where(*conditions).group_by(status_col)
    ).all())
    if status in STATUSES:
        conditions.append(status_col == status)
    total = db.scalar(select(func.count()).select_from(R).join(User, User.id == R.user_id).where(*conditions)) or 0
    rows = db.execute(
        select(R, User.email, User.full_name, lifter.full_name, status_col)
        .join(User, User.id == R.user_id)
        .outerjoin(lifter, lifter.id == R.lifted_by)
        .where(*conditions)
        .order_by(R.created_at.desc(), R.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    # Case gần nhất của mỗi tài khoản trên trang (ưu tiên case còn mở) để bấm sang xem bằng chứng
    user_ids = {r.user_id for r, *_ in rows}
    cases: dict[int, str] = {}
    if user_ids:
        open_first = case((RiskCase.status.in_(("OPEN", "IN_REVIEW")), 0), else_=1)
        for uid, code in db.execute(
            select(RiskCase.primary_user_id, RiskCase.case_code)
            .where(RiskCase.primary_user_id.in_(user_ids))
            .order_by(open_first.desc(), RiskCase.opened_at.asc())  # bản ghi sau ghi đè bản ghi trước
        ).all():
            cases[uid] = code
    trust = {uid: latest_trust(db, uid) for uid in user_ids}

    items = [
        {
            "id": r.id, "user_id": r.user_id, "user_email": email, "user_name": name, "kind": r.kind,
            "reason": r.reason, "source": r.source, "status": st, "created_at": r.created_at,
            "expires_at": r.expires_at, "lifted_at": r.lifted_at, "lifted_by_name": lifted_by,
            "lift_reason": r.lift_reason, "case_code": cases.get(r.user_id), "trust_score": trust.get(r.user_id),
        }
        for r, email, name, lifted_by, st in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size,
            "status_counts": {s: int(counts.get(s, 0)) for s in STATUSES}}
