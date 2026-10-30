from datetime import datetime

from sqlalchemy import BigInteger, CHAR, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Trạng thái đơn
PENDING_REVIEW = "PENDING_REVIEW"  # Risk Engine giữ đơn chờ nhân viên duyệt (module risk)
CONFIRMED = "CONFIRMED"
SHIPPING = "SHIPPING"
DELIVERED = "DELIVERED"
DELIVERY_FAILED = "DELIVERY_FAILED"
CANCELLED = "CANCELLED"
REJECTED = "REJECTED"  # nhân viên từ chối sau khi xem xét

COD = "COD"
PREPAID = "PREPAID"


class Address(Base):
    """Địa chỉ giao hàng. norm_hash là bản băm của địa chỉ đã chuẩn hóa, để đếm
    "bao nhiêu tài khoản dùng chung một địa chỉ" (luật R03)."""

    __tablename__ = "addresses"
    __table_args__ = (
        Index("ix_addresses_norm_hash_created", "norm_hash", "created_at"),
        UniqueConstraint("user_id", "norm_hash", name="uq_addresses_user_norm_hash"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    line: Mapped[str] = mapped_column(String(255))
    ward: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    province: Mapped[str] = mapped_column(String(100))
    norm_hash: Mapped[str] = mapped_column(CHAR(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_idempotency_key"),
        Index("ix_orders_user_payment_status", "user_id", "payment_method", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_code: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"))
    status: Mapped[str] = mapped_column(String(20))
    payment_method: Mapped[str] = mapped_column(String(10))
    payment_status: Mapped[str] = mapped_column(String(10))  # UNPAID | PAID
    subtotal: Mapped[int] = mapped_column(BigInteger)
    discount: Mapped[int] = mapped_column(BigInteger, default=0)
    total: Mapped[int] = mapped_column(BigInteger)
    voucher_code: Mapped[str | None] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    product_name: Mapped[str] = mapped_column(String(160))  # chụp lại lúc đặt
    category: Mapped[str] = mapped_column(String(32))
    unit_price: Mapped[int] = mapped_column(BigInteger)  # chụp lại lúc đặt
    quantity: Mapped[int] = mapped_column(Integer)


class ShipmentEvent(Base):
    """Nhật ký giao hàng (chỉ ghi thêm). Trong mô phỏng, nhân viên hoặc Simulator bấm thay đơn vị vận chuyển."""

    __tablename__ = "shipment_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    note: Mapped[str] = mapped_column(String(255), default="")
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
