from datetime import datetime

from pydantic import BaseModel


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
    user_email: str
    user_name: str
    order_code: str | None
    hits: list[HitOut]
