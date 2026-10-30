from pydantic import BaseModel, Field


class AddItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class UpdateItemIn(BaseModel):
    quantity: int = Field(ge=1, le=99)


class ApplyVoucherIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)


class CartItemOut(BaseModel):
    product_id: int
    slug: str
    name: str
    category: str
    image_url: str | None
    unit_price: int
    quantity: int
    stock: int
    line_total: int


class CartVoucherOut(BaseModel):
    code: str
    description: str
    discount: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    item_count: int
    subtotal: int
    discount: int
    total: int
    voucher: CartVoucherOut | None
    # Thông báo khi hệ thống tự gỡ voucher (ví dụ giỏ giảm xuống dưới giá trị tối thiểu)
    notice: str | None = None
