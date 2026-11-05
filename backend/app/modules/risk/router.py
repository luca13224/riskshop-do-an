from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, RISK_MANAGER, STAFF_ROLES, User
from app.core.errors import AppError
from app.modules.risk import backtest, graph, rules_admin, service
from app.modules.risk.schemas import (
    BacktestIn,
    DecisionOut,
    LiftRestrictionIn,
    NewVersionIn,
    RestrictionOut,
    RuleOut,
    RuleVersionOut,
)

router = APIRouter(prefix="/console/risk", tags=["risk"], dependencies=[Depends(require_roles(*STAFF_ROLES))])


@router.get("/decisions", response_model=list[DecisionOut])
def recent_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    after_id: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_recent(db, limit=limit, after_id=after_id)


@router.get("/rules", response_model=list[RuleOut])
def rules(db: Session = Depends(get_db)):
    return rules_admin.list_rules(db)


@router.get("/rules/{code}/versions", response_model=list[RuleVersionOut])
def rule_versions(code: str, db: Session = Depends(get_db)):
    return rules_admin.list_versions(db, code)


@router.post("/rules/{code}/versions", response_model=RuleOut)
def new_rule_version(
    code: str,
    data: NewVersionIn,
    # Tách bạch nhiệm vụ: Analyst xử lý case nhưng KHÔNG được sửa luật
    user: User = Depends(require_roles(RISK_MANAGER, ADMIN)),
    db: Session = Depends(get_db),
):
    return rules_admin.create_version(db, user, code, data.params, data.enabled, data.change_note)


# Chạy thử luật trên quyết định cũ: chỉ đọc, nên mọi nhân viên đều dùng được (sửa luật thật vẫn cần Risk Manager)
@router.post("/rules/{code}/backtest")
def backtest_rule(code: str, data: BacktestIn, db: Session = Depends(get_db)) -> dict:
    return backtest.backtest(db, code, data.params, data.enabled, data.days)


# Đồ thị liên kết: các tài khoản dính với nhau qua thiết bị / IP / địa chỉ giao hàng (2 bước, 30 ngày)
@router.get("/graph/{user_id}")
def link_graph(user_id: int, db: Session = Depends(get_db)) -> dict:
    result = graph.link_graph(db, user_id)
    if result is None:
        raise AppError("USER_NOT_FOUND", "Không tìm thấy khách hàng.", 404)
    return result



# ---------- Khóa quyền mua hàng (ADR-010) ----------
@router.get("/users/{user_id}/restriction", response_model=RestrictionOut | None)
def user_restriction(user_id: int, db: Session = Depends(get_db)):
    r = service.active_restriction(db, user_id)
    return service.restriction_info(r) if r else None


@router.post("/users/{user_id}/restriction/ban", response_model=RestrictionOut)
def ban_user(
    user_id: int,
    data: LiftRestrictionIn,  # cùng ràng buộc: bắt buộc lý do 10–255 ký tự
    user: User = Depends(require_roles(RISK_MANAGER, ADMIN)),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None or target.role != "customer":
        raise AppError("USER_NOT_FOUND", "Không tìm thấy khách hàng.", 404)
    r = service.ban(db, user_id, user.id, data.reason)
    db.commit()
    return service.restriction_info(r)


@router.post("/users/{user_id}/restriction/lift", response_model=RestrictionOut | None)
def lift_user_restriction(
    user_id: int,
    data: LiftRestrictionIn,
    # Gỡ khóa là quyết định nhạy cảm: chỉ Risk Manager / Admin, bắt buộc lý do, có audit
    user: User = Depends(require_roles(RISK_MANAGER, ADMIN)),
    db: Session = Depends(get_db),
):
    if service.lift_restrictions(db, user_id, user.id, data.reason) == 0:
        raise AppError("NO_ACTIVE_RESTRICTION", "Tài khoản không có khóa nào đang hiệu lực.", 409)
    db.commit()
    return None
