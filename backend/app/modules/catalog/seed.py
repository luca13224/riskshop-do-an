"""Dữ liệu sản phẩm mẫu cho demo. Chạy lại an toàn: sản phẩm đã có (theo SKU) thì cập nhật, chưa có thì thêm.

    python -m app.modules.catalog.seed

Tên và giá là dữ liệu tự đặt cho shop mô phỏng, không phải hàng của thương hiệu thật.
Không dùng ảnh bên ngoài (để demo chạy offline): frontend tự vẽ ảnh minh họa theo danh mục.
"""

import re
import sys
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.modules.catalog.models import Product

# (sku, tên, danh mục, giá VND, tồn kho, mô tả)
PRODUCTS = [
    ("AU-001", "Tai nghe không dây Aria", "audio", 590_000, 120, "Tai nghe nhét tai, pin 24 giờ kèm hộp sạc, chống nước nhẹ."),
    ("AU-002", "Loa bluetooth Pebble Mini", "audio", 450_000, 80, "Loa nhỏ gọn cầm tay, âm trầm khỏe, kết nối 2 thiết bị."),
    ("AU-003", "Tai nghe chụp tai Studio X", "audio", 1_890_000, 35, "Chống ồn chủ động, đệm tai êm, gập gọn khi mang theo."),
    ("CP-001", "Bàn phím cơ Kite 75%", "computer", 1_290_000, 60, "Bố cục 75%, switch thay nóng, đèn nền trắng."),
    ("CP-002", "Chuột không dây Glide", "computer", 390_000, 150, "Cảm biến chính xác, pin sạc, kết nối 2.4GHz và bluetooth."),
    ("CP-003", "Màn hình 27 inch ViewPro", "computer", 5_490_000, 20, "Tấm nền IPS 2K, 75Hz, viền mỏng, chân xoay linh hoạt."),
    ("CP-004", "Giá đỡ laptop nhôm Lift", "computer", 320_000, 90, "Nâng màn hình ngang tầm mắt, gấp gọn, tản nhiệt tốt."),
    ("HM-001", "Bình giữ nhiệt Lumi 500ml", "home", 249_000, 200, "Giữ nóng 12 giờ, giữ lạnh 24 giờ, inox 304."),
    ("HM-002", "Đèn bàn LED Nova", "home", 420_000, 70, "3 chế độ màu, điều chỉnh độ sáng, cổng sạc USB."),
    ("HM-003", "Nồi chiên không dầu Crispy 5L", "home", 1_650_000, 40, "Dung tích 5 lít, 8 chế độ nấu cài sẵn, lòng nồi chống dính."),
    ("FS-001", "Áo khoác gió Breeze", "fashion", 520_000, 110, "Chống nước nhẹ, có mũ, gấp gọn vào túi."),
    ("FS-002", "Giày chạy bộ Stride", "fashion", 990_000, 55, "Đế êm, thoáng khí, phù hợp chạy đường dài."),
    ("FS-003", "Ví da Classic", "fashion", 350_000, 95, "Da bò thật, nhiều ngăn thẻ, nhỏ gọn bỏ túi."),
    ("SP-001", "Balo chống nước Trek 20L", "sport", 459_000, 85, "Ngăn laptop 15.6 inch, vải chống nước, quai đeo êm."),
    ("SP-002", "Thảm tập yoga Flow", "sport", 280_000, 130, "Dày 6mm, chống trơn, kèm dây đeo."),
    ("SP-003", "Đồng hồ thông minh Pulse", "sport", 2_390_000, 30, "Đo nhịp tim, GPS, chống nước 5ATM, pin 7 ngày."),
]


def slugify(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def seed(session: Session | None = None) -> int:
    created = 0
    with (session or SessionLocal()) as db:
        for sku, name, category, price, stock, description in PRODUCTS:
            product = db.scalar(select(Product).where(Product.sku == sku))
            if product is None:
                product = Product(sku=sku)
                db.add(product)
                created += 1
            product.name = name
            product.slug = f"{slugify(name)}-{sku.lower()}"
            product.category = category
            product.price = price
            product.stock = stock
            product.description = description
            product.is_active = True
        db.commit()
    return created


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = seed()
    print(f"Đã thêm {n} sản phẩm mới, tổng {len(PRODUCTS)} sản phẩm mẫu.")
