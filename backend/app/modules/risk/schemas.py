from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.privacy import MaskedEmail


class HitOut(BaseModel):
    rule_code: str
    points: int
    strength: str
    reason_text: str


class TrustDeductionOut(BaseModel):
    rule_code: str
    rule_name: str
    points: int  # dương: bị trừ; âm: được cộng lại


class TrustOut(BaseModel):
    """Điểm tin cậy tài khoản tại thời điểm quyết định (lớp 1, bộ luật v3) và "sổ trừ điểm"."""

    score: int
    tier: str
    deductions: list[TrustDeductionOut]


class RestrictionOut(BaseModel):
    """Khóa quyền mua hàng đang hiệu lực (ADR-010). until = None: vô thời hạn."""

    kind: str  # purchase_cooldown | purchase_ban
    since: str
    until: str | None
    reason: str


class RestrictionRowOut(BaseModel):
    """Một lệnh khóa trong danh sách Console. status: active | expired | lifted (tính lúc đọc)."""

    id: int
    user_id: int
    user_email: MaskedEmail
    user_name: str
    kind: str
    reason: str
    source: str  # auto | staff
    status: str
    created_at: datetime
    expires_at: datetime | None
    lifted_at: datetime | None
    lifted_by_name: str | None
    lift_reason: str | None
    case_code: str | None  # case gần nhất của tài khoản (ưu tiên case còn mở)
    trust_score: int | None  # điểm tin cậy ở lần chấm gần nhất


class RestrictionPage(BaseModel):
    items: list[RestrictionRowOut]
    total: int
    page: int
    page_size: int
    status_counts: dict[str, int]  # đã áp bộ lọc loại / từ khóa, chưa áp bộ lọc trạng thái


class LiftRestrictionIn(BaseModel):
    reason: str = Field(min_length=10, max_length=255)


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
    trust: TrustOut | None = None  # None: quyết định trước bộ luật v3
    restriction: RestrictionOut | None = None  # quyết định này kích hoạt hoặc bị chặn vì khóa tài khoản


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


class BacktestIn(BaseModel):
    """Chạy thử tham số mới của một luật trên các quyết định cũ (không lưu gì)."""
    params: dict
    enabled: bool = True
    days: int = Field(default=30, ge=1, le=90)
