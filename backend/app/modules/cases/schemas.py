from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.privacy import MaskedEmail
from app.modules.risk.schemas import DecisionOut


class CaseSummaryOut(BaseModel):
    case_code: str
    policy: str
    status: str
    cluster_label: str
    primary_user_id: int
    primary_user_email: MaskedEmail
    decision_count: int
    max_score: int
    assigned_to_name: str | None
    opened_at: datetime
    closed_at: datetime | None


class LinkedAccountOut(BaseModel):
    user_id: int
    email: MaskedEmail
    full_name: str
    created_at: datetime
    last_seen_at: datetime


class CaseActionOut(BaseModel):
    action: str
    from_status: str | None
    to_status: str
    note: str
    staff_name: str | None
    created_at: datetime


class OrderBriefOut(BaseModel):
    order_code: str
    status: str
    payment_method: str
    total: int
    created_at: datetime
    area: str


class CaseDetailOut(CaseSummaryOut):
    outcome_reason: str | None
    linked_accounts: list[LinkedAccountOut]
    decisions: list[DecisionOut]
    actions: list[CaseActionOut]
    order: OrderBriefOut | None


class ResolveIn(BaseModel):
    outcome: Literal["CONFIRMED_ABUSE", "CLEARED"]
    note: str = Field(max_length=1000)

    @field_validator("note")
    @classmethod
    def _note_required(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Cần ghi lý do kết luận (tối thiểu 10 ký tự)")
        return v
