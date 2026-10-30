"""Risk API giả cho spike WooCommerce connector.

Mục đích DUY NHẤT: kiểm chứng plugin connector làm được 3 việc
(gỡ coupon, ẩn COD, chuyển đơn sang On hold) dựa trên phản hồi của Risk Service.
Đây KHÔNG phải Risk Engine thật: quyết định được kích hoạt bằng "mã kích hoạt" cố định
để test cho dễ, không có luật hay chấm điểm.

Mã kích hoạt khi test:
- Coupon có chữ "FARM"            -> gỡ coupon đó (ALLOW_WITH_RESTRICTION)
- Email có chữ "+nocod"           -> ẩn COD (ALLOW_WITH_RESTRICTION)
- Email có chữ "+review"          -> giữ đơn chờ duyệt (REVIEW -> On hold)
- Email có chữ "+block"           -> từ chối đặt đơn (BLOCK)
- Còn lại                         -> ALLOW

Chạy: uvicorn main:app --port 8000 --reload
Tài liệu API tự sinh: http://127.0.0.1:8000/docs
"""

import logging
import time
import uuid
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("risk-mock")

app = FastAPI(title="Risk Service (mock for spike)", version="0.0.1")


class EvaluateRequest(BaseModel):
    """Sự kiện mà shop gửi sang để xin quyết định."""

    event: Literal["cart_update", "payment_methods", "checkout"]
    customer_email: str = ""
    coupon_codes: list[str] = Field(default_factory=list)
    payment_method: str | None = None
    order_total: float = 0


class Actions(BaseModel):
    """Những việc cụ thể shop phải làm. Connector chỉ làm theo, không tự quyết."""

    remove_coupons: list[str] = Field(default_factory=list)
    disable_cod: bool = False
    hold_order: bool = False
    block: bool = False


class EvaluateResponse(BaseModel):
    decision_id: str
    decision: Literal["ALLOW", "ALLOW_WITH_RESTRICTION", "REVIEW", "BLOCK"]
    actions: Actions
    reason_codes: list[str]
    customer_message: str  # thông điệp chung chung, không lộ luật


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    started = time.perf_counter()
    email = req.customer_email.lower()
    actions = Actions()
    reasons: list[str] = []
    decision = "ALLOW"
    message = ""

    farm_coupons = [c for c in req.coupon_codes if "farm" in c.lower()]
    if farm_coupons:
        actions.remove_coupons = farm_coupons
        reasons.append("MOCK_FARM_COUPON")
        decision = "ALLOW_WITH_RESTRICTION"
        message = "Một số mã giảm giá không áp dụng được cho đơn hàng này."

    if "+nocod" in email:
        actions.disable_cod = True
        reasons.append("MOCK_NO_COD")
        decision = "ALLOW_WITH_RESTRICTION"

    # chỉ ra quyết định giữ/chặn ở bước checkout, vì lúc đó mới có đơn hàng
    if req.event == "checkout" and "+review" in email:
        actions.hold_order = True
        reasons.append("MOCK_REVIEW")
        decision = "REVIEW"

    if req.event == "checkout" and "+block" in email:
        actions.block = True
        reasons.append("MOCK_BLOCK")
        decision = "BLOCK"
        message = "Hiện chưa thể xử lý đơn hàng. Vui lòng liên hệ bộ phận hỗ trợ."

    resp = EvaluateResponse(
        decision_id=str(uuid.uuid4()),
        decision=decision,
        actions=actions,
        reason_codes=reasons,
        customer_message=message,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    log.info(
        "event=%s decision=%s reasons=%s elapsed_ms=%.2f",
        req.event, decision, reasons, elapsed_ms,
    )
    return resp
