from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, User
from app.modules.lab import service
from app.modules.lab.scenarios import SCENARIOS

router = APIRouter(prefix="/console/lab", tags=["lab"])
admin = require_roles(ADMIN)


class ScenarioOut(BaseModel):
    code: str
    title: str
    scene: str
    description: str
    expected: str


class RunIn(BaseModel):
    scenario: str


class RunOut(BaseModel):
    id: int
    scenario: str
    status: str
    run_tag: str
    steps: list[dict]
    summary: str | None
    passed: bool | None
    created_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/scenarios", response_model=list[ScenarioOut])
def scenarios(_: User = Depends(admin)):
    service.require_demo_mode()
    return [ScenarioOut(code=s.code, title=s.title, scene=s.scene, description=s.description, expected=s.expected)
            for s in SCENARIOS.values()]


@router.post("/runs", response_model=RunOut, status_code=status.HTTP_202_ACCEPTED)
def start(data: RunIn, user: User = Depends(admin), db: Session = Depends(get_db)):
    # 202 Accepted: đã nhận yêu cầu, kịch bản chạy nền trong worker
    return service.start_run(db, user, data.scenario)


@router.get("/runs", response_model=list[RunOut])
def runs(_: User = Depends(admin), db: Session = Depends(get_db)):
    service.require_demo_mode()
    return service.list_runs(db)


@router.get("/runs/{run_id}", response_model=RunOut)
def run(run_id: int, _: User = Depends(admin), db: Session = Depends(get_db)):
    service.require_demo_mode()
    return service.get_run(db, run_id)
