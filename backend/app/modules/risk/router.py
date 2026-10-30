from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, RISK_MANAGER, STAFF_ROLES, User
from app.modules.risk import rules_admin, service
from app.modules.risk.schemas import DecisionOut, NewVersionIn, RuleOut, RuleVersionOut

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
