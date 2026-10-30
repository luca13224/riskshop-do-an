"""Bảng của module catalog (xem docs/ERD.md, nhóm "Bán hàng")."""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Danh mục cố định cho demo (mã -> tên hiển thị). Gian hàng chỉ bán đồ công nghệ (ADR-005).
CATEGORIES = {
    "audio": "Âm thanh",
    "laptop": "Laptop & máy tính bảng",
    "monitor": "Màn hình",
    "gear": "Bàn phím & chuột",
    "phone": "Điện thoại & phụ kiện",
    "smart": "Thiết bị thông minh",
}


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_active_category", "is_active", "category"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[int] = mapped_column(BigInteger)  # VND, số nguyên
    image_url: Mapped[str | None] = mapped_column(String(500))
    # Thông số kỹ thuật dạng danh sách [nhãn, giá trị] để giữ đúng thứ tự hiển thị
    specs: Mapped[list | None] = mapped_column(JSON)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
