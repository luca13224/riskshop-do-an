"""Bảng của module catalog (xem docs/ERD.md, nhóm "Bán hàng")."""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Danh mục cố định cho demo (mã -> tên hiển thị). Đủ để lọc trên trang chủ, chưa cần bảng riêng.
CATEGORIES = {
    "audio": "Âm thanh",
    "computer": "Máy tính & phụ kiện",
    "home": "Nhà cửa & đời sống",
    "fashion": "Thời trang",
    "sport": "Thể thao & du lịch",
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
    stock: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
