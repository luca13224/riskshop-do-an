from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.privacy import MaskedEmail
from app.modules.risk.schemas import DecisionOut

Policy = Literal["voucher", "cod"]


def _min_text(v: str, n: int, what: str) -> str:
    v = v.strip()
    if len(v) < n:
        raise ValueError(f"{what} cần tối thiểu {n} ký tự")
    return v


class EligibleOut(BaseModel):
    """Một lần khách bị hạn chế mà có thể khiếu nại. KHÔNG có luật hay điểm: không lộ luật cho kẻ gian."""

    decision_id: str  # public_id của quyết định
    policy: Policy
    label: str
    context: str
    created_at: datetime
    order_code: str | None
    order_status: str | None
    open_appeal: str | None  # mã khiếu nại đang mở cho chính sách này (nếu có)


class AppealCreateIn(BaseModel):
    decision_id: str = Field(max_length=36)
    policy: Policy
    message: str = Field(max_length=1000)

    @field_validator("message")
    @classmethod
    def _message(cls, v: str) -> str:
        return _min_text(v, 20, "Nội dung khiếu nại")


class AppealOut(BaseModel):
    appeal_code: str
    policy: Policy
    label: str
    status: str
    message: str
    response: str | None
    order_code: str | None
    created_at: datetime
    resolved_at: datetime | None


class StaffAppealOut(AppealOut):
    user_id: int
    user_email: MaskedEmail
    user_name: str
    handled_by_name: str | None


class StaffAppealDetailOut(StaffAppealOut):
    decision: DecisionOut | None
    active_exemptions: list[str]
    other_appeals: int  # số khiếu nại khác của cùng khách (dấu hiệu lạm dụng kênh khiếu nại)


class ResolveIn(BaseModel):
    outcome: Literal["ACCEPTED", "REJECTED"]
    response: str = Field(max_length=1000)

    @field_validator("response")
    @classmethod
    def _response(cls, v: str) -> str:
        return _min_text(v, 10, "Câu trả lời cho khách")
