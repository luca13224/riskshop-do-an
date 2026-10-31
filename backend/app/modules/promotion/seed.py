"""Voucher mẫu cho demo. Chạy lại an toàn (theo mã).

    python -m app.modules.promotion.seed
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.modules.promotion.models import FIXED, PERCENT, Voucher

# Mã cấp sẵn vào túi voucher khi tạo tài khoản (Trust Score, bộ luật v3; trước đây là mã NGUOIMOI)
WELCOME_CODE = "NGUOIMOI"

VOUCHERS = [
    dict(
        code=WELCOME_CODE,
        description="Giảm 50.000đ cho thành viên mới, đơn từ 200.000đ",
        discount_type=FIXED,
        amount=50_000,
        min_order_value=200_000,
        new_user_only=True,
        risk_checked=True,  # đây là voucher bị farm trong kịch bản demo
        min_trust=50,
    ),
    dict(
        code="GIAM10",
        description="Giảm 10% tối đa 100.000đ, đơn từ 500.000đ",
        discount_type=PERCENT,
        amount=10,
        max_discount=100_000,
        min_order_value=500_000,
        risk_checked=True,  # bộ luật v3: mọi mã đều qua Risk Engine để xét điểm tin cậy
        min_trust=70,  # mã giá trị cao hơn: khóa sớm hơn khi điểm tin cậy giảm
    ),
]


def seed(session: Session | None = None) -> int:
    created = 0
    with (session or SessionLocal()) as db:
        for data in VOUCHERS:
            voucher = db.scalar(select(Voucher).where(Voucher.code == data["code"]))
            if voucher is None:
                voucher = Voucher(code=data["code"])
                db.add(voucher)
                created += 1
            for key, value in data.items():
                setattr(voucher, key, value)
            voucher.is_active = True
        # Mã không còn trong danh sách (ví dụ NGUOIMOI cũ) thì ngừng phát hành, giữ dữ liệu để truy vết đơn cũ
        codes = [v["code"] for v in VOUCHERS]
        for old in db.scalars(select(Voucher).where(Voucher.code.not_in(codes), Voucher.is_active.is_(True))):
            old.is_active = False
        db.commit()
    return created


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Đã thêm {seed()} voucher mới, tổng {len(VOUCHERS)} voucher mẫu.")
