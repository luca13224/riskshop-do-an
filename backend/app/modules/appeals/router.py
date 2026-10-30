"""Endpoint khiếu nại: /api/appeals (khách hàng) và /api/console/appeals (nhân viên)."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.appeals import service
from app.modules.appeals.schemas import (
    AppealCreateIn,
    AppealOut,
    EligibleOut,
    ResolveIn,
    StaffAppealDetailOut,
    StaffAppealOut,
)
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, CUSTOMER, RISK_MANAGER, STAFF_ROLES, User

router = APIRouter(tags=["appeals"])
customer = require_roles(CUSTOMER)
staff = require_roles(*STAFF_ROLES)
# Kết luận khiếu nại là bước "xét lại" nên chỉ cấp quản lý (nguyên tắc bốn mắt, ADR-006)
reviewer = require_roles(RISK_MANAGER, ADMIN)


@router.get("/appeals/eligible", response_model=list[EligibleOut])
def eligible(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.eligible(db, user)


@router.get("/appeals", response_model=list[AppealOut])
def my_appeals(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.list_mine(db, user)


@router.post("/appeals", response_model=AppealOut, status_code=status.HTTP_201_CREATED)
def create(data: AppealCreateIn, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.create(db, user, data.decision_id, data.policy, data.message)


@router.get("/console/appeals", response_model=list[StaffAppealOut])
def list_appeals(
    status: Literal["OPEN", "ACCEPTED", "REJECTED", "ALL"] = Query(default="OPEN"),
    _: User = Depends(staff),
    db: Session = Depends(get_db),
):
    return service.list_appeals(db, None if status == "ALL" else status)


@router.get("/console/appeals/{code}", response_model=StaffAppealDetailOut)
def get_appeal(code: str, _: User = Depends(staff), db: Session = Depends(get_db)):
    return service.get_appeal(db, code)


@router.post("/console/appeals/{code}/resolve", response_model=StaffAppealDetailOut)
def resolve(code: str, data: ResolveIn, user: User = Depends(reviewer), db: Session = Depends(get_db)):
    return service.resolve(db, user, code, data.outcome, data.response)
