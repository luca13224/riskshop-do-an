import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_PHONE_RE = re.compile(r"^0\d{9}$")


class AddressIn(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=120)
    phone: str
    line: str = Field(min_length=3, max_length=255, description="Số nhà, tên đường")
    ward: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)
    province: str = Field(min_length=1, max_length=100)

    @field_validator("recipient_name", "line", "ward", "district", "province")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("Không được để trống")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if not _PHONE_RE.match(v):
            raise ValueError("Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")
        return v


class CheckoutIn(BaseModel):
    address: AddressIn
    payment_method: Literal["COD", "PREPAID"]


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    category: str
    unit_price: int
    quantity: int
    line_total: int


class ShipmentEventOut(BaseModel):
    status: str
    note: str
    occurred_at: datetime


class OrderOut(BaseModel):
    order_code: str
    status: str
    payment_method: str
    payment_status: str
    subtotal: int
    discount: int
    total: int
    voucher_code: str | None
    created_at: datetime
    items: list[OrderItemOut]
    address: AddressIn
    events: list[ShipmentEventOut]


class OrderSummaryOut(BaseModel):
    order_code: str
    status: str
    payment_method: str
    total: int
    item_count: int
    created_at: datetime


class StaffOrderOut(OrderSummaryOut):
    customer_email: str
    customer_name: str


class ShipmentUpdateIn(BaseModel):
    status: Literal["SHIPPING", "DELIVERED", "DELIVERY_FAILED"]
    note: str = Field(default="", max_length=255)
