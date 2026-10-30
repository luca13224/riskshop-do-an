from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.privacy import MaskedEmail


class HitOut(BaseModel):
    rule_code: str
    points: int
    strength: str
    reason_text: str


class DecisionOut(BaseModel):
    id: int
    public_id: str
    created_at: datetime
    context: str
    decision: str
    score: int
    policy_scores: dict[str, int]
    actions: dict[str, bool]
    latency_ms: float
    error: str | None
    user_id: int
    user_email: MaskedEmail
    user_name: str
    order_code: str | None
    hits: list[HitOut]


class RuleVersionOut(BaseModel):
    version: int
    params: dict
    contexts: list[str]
    enabled: bool
    reason_template: str
    change_note: str
    created_by_name: str | None
    created_at: datetime


class RuleOut(BaseModel):
    code: str
    name: str
    rule_type: str
    strength: str
    policies: list[str]
    hit_count_7d: int
    active: RuleVersionOut


class NewVersionIn(BaseModel):
    params: dict
    enabled: bool
    change_note: str = Field(max_length=255)

    @field_validator("change_note")
    @classmethod
    def _note(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Cần ghi lý do thay đổi (tối thiểu 10 ký tự)")
        return v
