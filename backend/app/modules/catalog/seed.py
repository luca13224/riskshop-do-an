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
# Giữ nguyên SKU cũ của các món còn bán (AU-001, CP-003, SP-003...) vì Attack Lab, demo reset và simulator dùng chúng.
# Bậc giá cố ý trải rộng: dưới 500 nghìn, 1–3 triệu, và từ 3 triệu (kịch bản COD giá trị cao).
PRODUCTS = [
    # Âm thanh
    ("AU-001", "Tai nghe không dây Aria", "audio", 590_000, 120, "Tai nghe nhét tai, pin 24 giờ kèm hộp sạc, chống nước nhẹ."),
    ("AU-002", "Loa bluetooth Pebble Mini", "audio", 450_000, 80, "Loa nhỏ gọn cầm tay, âm trầm khỏe, kết nối 2 thiết bị."),
    ("AU-003", "Tai nghe chụp tai Studio X", "audio", 1_890_000, 35, "Chống ồn chủ động, đệm tai êm, gập gọn khi mang theo."),
    ("AU-004", "Loa soundbar Cinema 300W", "audio", 3_290_000, 25, "Loa thanh kèm loa siêu trầm không dây, kết nối HDMI eARC."),
    # Laptop & máy tính bảng
    ("LT-001", "Laptop mỏng nhẹ Aero 14", "laptop", 18_990_000, 15, "Màn hình 14 inch 2.8K, 16GB RAM, SSD 512GB, nặng 1,2 kg."),
    ("LT-002", "Máy tính bảng Slate 11", "laptop", 8_490_000, 25, "Màn hình 11 inch 120Hz, hỗ trợ bút cảm ứng, pin 10 giờ."),
    ("LT-003", "Hub USB-C 7 trong 1 Dock", "laptop", 690_000, 100, "HDMI 4K, 3 cổng USB-A, đọc thẻ SD, sạc xuyên 100W."),
    ("CP-004", "Giá đỡ laptop nhôm Lift", "laptop", 320_000, 90, "Nâng màn hình ngang tầm mắt, gấp gọn, tản nhiệt tốt."),
    # Màn hình
    ("CP-003", "Màn hình 27 inch ViewPro", "monitor", 5_490_000, 20, "Tấm nền IPS 2K, 75Hz, viền mỏng, chân xoay linh hoạt."),
    ("MN-001", "Màn hình 24 inch ViewLite", "monitor", 2_790_000, 40, "Tấm nền IPS Full HD, 100Hz, chống chói, có cổng USB-C."),
    ("MN-002", "Màn hình cong 34 inch UltraWide", "monitor", 9_990_000, 12, "Tỷ lệ 21:9, độ phân giải WQHD, 144Hz, độ cong 1500R."),
    ("MN-003", "Đèn treo màn hình Halo", "monitor", 450_000, 70, "Chiếu sáng mặt bàn không lóa màn hình, chỉnh nhiệt độ màu."),
    # Bàn phím & chuột
    ("CP-001", "Bàn phím cơ Kite 75%", "gear", 1_290_000, 60, "Bố cục 75%, switch thay nóng, đèn nền trắng."),
    ("CP-002", "Chuột không dây Glide", "gear", 390_000, 150, "Cảm biến chính xác, pin sạc, kết nối 2.4GHz và bluetooth."),
    ("GR-001", "Lót chuột cỡ lớn Desk XL", "gear", 199_000, 200, "Kích thước 90 x 40 cm, bề mặt mịn, viền khâu chống sờn."),
    ("GR-002", "Webcam 2K Clear", "gear", 890_000, 60, "Độ phân giải 2K, tự lấy nét, micro kép lọc ồn."),
    # Điện thoại & phụ kiện
    ("PH-001", "Cáp sạc USB-C bện dù 2m", "phone", 149_000, 300, "Sạc nhanh 100W, vỏ bện dù bền, đầu nhôm."),
    ("PH-002", "Củ sạc nhanh GaN 65W", "phone", 590_000, 120, "3 cổng sạc, nhỏ gọn, sạc được cả laptop."),
    ("PH-003", "Sạc dự phòng Volt 20.000mAh", "phone", 690_000, 90, "Sạc nhanh 2 chiều 22.5W, màn hình hiển thị phần trăm pin."),
    ("PH-004", "Điện thoại Nova X", "phone", 12_990_000, 20, "Màn hình 6,7 inch 120Hz, camera 50MP, pin 5000mAh."),
    # Thiết bị thông minh
    ("SP-003", "Đồng hồ thông minh Pulse", "smart", 2_390_000, 30, "Đo nhịp tim, GPS, chống nước 5ATM, pin 7 ngày."),
    ("SM-001", "Camera an ninh Wi-Fi Eye 2K", "smart", 790_000, 80, "Xoay 360 độ, nhìn đêm có màu, đàm thoại hai chiều."),
    ("SM-002", "Ổ cắm thông minh Plug", "smart", 249_000, 200, "Bật tắt từ xa, hẹn giờ, đo điện năng tiêu thụ."),
    ("SM-003", "Vòng đeo sức khỏe Band 4", "smart", 690_000, 100, "Đo nhịp tim, giấc ngủ, SpO2, pin 14 ngày."),
]


# Thông số kỹ thuật hiển thị ở trang chi tiết (dữ liệu tự đặt cho shop mô phỏng)
SPECS = {
    "AU-001": [("Kết nối", "Bluetooth 5.3"), ("Thời lượng pin", "6 giờ, 24 giờ kèm hộp"), ("Chống nước", "IPX4"), ("Bảo hành", "12 tháng")],
    "AU-002": [("Công suất", "10W"), ("Kết nối", "Bluetooth 5.2, 2 thiết bị"), ("Thời lượng pin", "12 giờ"), ("Bảo hành", "12 tháng")],
    "AU-003": [("Chống ồn", "Chủ động (ANC)"), ("Kết nối", "Bluetooth 5.3, jack 3.5mm"), ("Thời lượng pin", "30 giờ"), ("Bảo hành", "12 tháng")],
    "AU-004": [("Tổng công suất", "300W"), ("Kênh", "2.1, loa siêu trầm không dây"), ("Kết nối", "HDMI eARC, quang, Bluetooth"), ("Bảo hành", "24 tháng")],
    "LT-001": [("CPU", "8 nhân, tiết kiệm điện"), ("RAM / SSD", "16GB / 512GB"), ("Màn hình", "14 inch 2.8K, 90Hz"), ("Trọng lượng", "1,2 kg"), ("Bảo hành", "24 tháng")],
    "LT-002": [("Màn hình", "11 inch, 120Hz"), ("Bộ nhớ", "8GB / 128GB"), ("Pin", "Khoảng 10 giờ"), ("Bảo hành", "12 tháng")],
    "LT-003": [("Cổng", "HDMI 4K, 3 x USB-A, SD, microSD, USB-C PD"), ("Sạc xuyên", "100W"), ("Chất liệu", "Nhôm"), ("Bảo hành", "12 tháng")],
    "CP-004": [("Chất liệu", "Nhôm nguyên khối"), ("Tương thích", "Laptop 10–17 inch"), ("Số nấc chỉnh", "6"), ("Bảo hành", "6 tháng")],
    "CP-003": [("Tấm nền", "IPS 27 inch"), ("Độ phân giải", "2560 x 1440"), ("Tần số quét", "75Hz"), ("Cổng", "HDMI, DisplayPort"), ("Bảo hành", "24 tháng")],
    "MN-001": [("Tấm nền", "IPS 24 inch"), ("Độ phân giải", "1920 x 1080"), ("Tần số quét", "100Hz"), ("Cổng", "HDMI, USB-C 65W"), ("Bảo hành", "24 tháng")],
    "MN-002": [("Tấm nền", "VA cong 34 inch, 1500R"), ("Độ phân giải", "3440 x 1440"), ("Tần số quét", "144Hz"), ("Bảo hành", "24 tháng")],
    "MN-003": [("Nguồn", "USB-C 5V"), ("Nhiệt độ màu", "2700K – 6500K"), ("Lắp đặt", "Kẹp trên màn hình, không khoan"), ("Bảo hành", "12 tháng")],
    "CP-001": [("Bố cục", "75%, 84 phím"), ("Switch", "Thay nóng, linear"), ("Kết nối", "USB-C, Bluetooth, 2.4GHz"), ("Bảo hành", "12 tháng")],
    "CP-002": [("Cảm biến", "Quang học, 26.000 DPI"), ("Kết nối", "2.4GHz, Bluetooth"), ("Pin", "Sạc USB-C, 70 giờ"), ("Bảo hành", "12 tháng")],
    "GR-001": [("Kích thước", "90 x 40 cm"), ("Độ dày", "4 mm"), ("Mặt đế", "Cao su chống trượt"), ("Bảo hành", "3 tháng")],
    "GR-002": [("Độ phân giải", "2K, 30 khung hình/giây"), ("Lấy nét", "Tự động"), ("Micro", "Kép, lọc ồn"), ("Bảo hành", "12 tháng")],
    "PH-001": [("Chiều dài", "2 m"), ("Công suất", "Tối đa 100W"), ("Vỏ", "Bện dù"), ("Bảo hành", "6 tháng")],
    "PH-002": [("Công suất", "65W"), ("Cổng", "2 x USB-C, 1 x USB-A"), ("Công nghệ", "GaN"), ("Bảo hành", "12 tháng")],
    "PH-003": [("Dung lượng", "20.000mAh"), ("Sạc nhanh", "22.5W hai chiều"), ("Cổng", "USB-C, 2 x USB-A"), ("Bảo hành", "12 tháng")],
    "PH-004": [("Màn hình", "6,7 inch OLED, 120Hz"), ("Bộ nhớ", "8GB / 256GB"), ("Camera", "50MP chính, 12MP góc rộng"), ("Pin", "5000mAh"), ("Bảo hành", "12 tháng")],
    "SP-003": [("Màn hình", "AMOLED 1,4 inch"), ("Cảm biến", "Nhịp tim, SpO2, GPS"), ("Chống nước", "5ATM"), ("Pin", "7 ngày"), ("Bảo hành", "12 tháng")],
    "SM-001": [("Độ phân giải", "2K"), ("Góc quay", "360 độ ngang, 110 độ dọc"), ("Lưu trữ", "Thẻ nhớ, đám mây"), ("Bảo hành", "12 tháng")],
    "SM-002": [("Tải tối đa", "16A / 3500W"), ("Kết nối", "Wi-Fi 2.4GHz"), ("Tính năng", "Hẹn giờ, đo điện năng"), ("Bảo hành", "12 tháng")],
    "SM-003": [("Màn hình", "AMOLED 1,1 inch"), ("Cảm biến", "Nhịp tim, SpO2, giấc ngủ"), ("Pin", "14 ngày"), ("Bảo hành", "12 tháng")],
}


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
            product.specs = [list(row) for row in SPECS.get(sku, [])]
            product.is_active = True
        # Sản phẩm cũ không còn trong danh sách thì ẩn đi (không xóa, vì đơn hàng cũ còn tham chiếu)
        skus = [row[0] for row in PRODUCTS]
        for old in db.scalars(select(Product).where(Product.sku.not_in(skus), Product.is_active.is_(True))):
            old.is_active = False
        db.commit()
    return created


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = seed()
    print(f"Đã thêm {n} sản phẩm mới, tổng {len(PRODUCTS)} sản phẩm mẫu.")
