import json
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, RISK_MANAGER, STAFF_ROLES
from app.modules.reports import service

router = APIRouter(prefix="/console", tags=["reports"])


@router.get("/reports/kpi", dependencies=[Depends(require_roles(*STAFF_ROLES))])
def kpi(days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)) -> dict[str, Any]:
    return service.kpi(db, days)


# Dashboard tổng quan: mọi nhân viên rủi ro đều xem được (email trong danh sách đã che)
@router.get("/dashboard", dependencies=[Depends(require_roles(*STAFF_ROLES))])
def dashboard(days: int = Query(default=7, ge=1, le=90), db: Session = Depends(get_db)) -> dict[str, Any]:
    return service.dashboard(db, days)


class AuditOut(BaseModel):
    id: int
    created_at: datetime
    action: str
    entity_type: str
    entity_id: str
    before_data: dict | None
    after_data: dict | None
    note: str | None
    actor_name: str | None
    actor_role: str | None

    @field_validator("before_data", "after_data", mode="before")
    @classmethod
    def _json(cls, v):
        # SQL thuần trả cột JSON dạng chuỗi
        return json.loads(v) if isinstance(v, str) else v


# Audit log: chỉ người giám sát (Risk Manager, Admin) xem được, kể cả xem thao tác của Analyst
@router.get("/audit", response_model=list[AuditOut], dependencies=[Depends(require_roles(RISK_MANAGER, ADMIN))])
def audit(
    limit: int = Query(default=100, ge=1, le=500),
    entity_type: Literal["case", "rule", "lab_run", "user"] | None = None,
    db: Session = Depends(get_db),
):
    return service.audit_logs(db, limit, entity_type)
