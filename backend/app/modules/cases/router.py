from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import STAFF_ROLES, User
from app.modules.cases import service
from app.modules.cases.schemas import CaseDetailOut, CaseSummaryOut, ResolveIn

router = APIRouter(prefix="/console/cases", tags=["cases"])
staff = require_roles(*STAFF_ROLES)


@router.get("", response_model=list[CaseSummaryOut])
def list_cases(
    status: Literal["ACTIVE", "CLOSED", "ALL"] = Query(default="ACTIVE"),
    _: User = Depends(staff),
    db: Session = Depends(get_db),
):
    return service.list_cases(db, None if status == "ALL" else status)


@router.get("/{code}", response_model=CaseDetailOut)
def get_case(code: str, _: User = Depends(staff), db: Session = Depends(get_db)):
    return service.get_case(db, code)


@router.post("/{code}/claim", response_model=CaseDetailOut)
def claim(code: str, user: User = Depends(staff), db: Session = Depends(get_db)):
    return service.claim(db, user, code)


@router.post("/{code}/resolve", response_model=CaseDetailOut)
def resolve(code: str, data: ResolveIn, user: User = Depends(staff), db: Session = Depends(get_db)):
    return service.resolve(db, user, code, data.outcome, data.note)
