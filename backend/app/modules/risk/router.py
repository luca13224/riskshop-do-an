from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import STAFF_ROLES
from app.modules.risk import service
from app.modules.risk.schemas import DecisionOut

router = APIRouter(prefix="/console/risk", tags=["risk"], dependencies=[Depends(require_roles(*STAFF_ROLES))])


@router.get("/decisions", response_model=list[DecisionOut])
def recent_decisions(
    limit: int = Query(default=50, ge=1, le=200),
    after_id: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_recent(db, limit=limit, after_id=after_id)
