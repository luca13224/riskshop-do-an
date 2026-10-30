"""Voucher mẫu cho demo. Chạy lại an toàn (theo mã).

    python -m app.modules.promotion.seed
"""

import sys

from sqlalchemy import select

from app.core.db import SessionLocal
from app.modules.promotion.models import FIXED, PERCENT, Voucher

VOUCHERS = [
    dict(
        code="TANTHU",
        description="Giảm 50.000đ cho thành viên mới, đơn từ 200.000đ",
        discount_type=FIXED,
        amount=50_000,
        min_order_value=200_000,
        new_user_only=True,
        risk_checked=True,  # đây là voucher bị farm trong kịch bản demo
    ),
    dict(
        code="GIAM10",
        description="Giảm 10% tối đa 100.000đ, đơn từ 500.000đ",
        discount_type=PERCENT,
        amount=10,
        max_discount=100_000,
        min_order_value=500_000,
    ),
]


def seed() -> int:
    created = 0
    with SessionLocal() as db:
        for data in VOUCHERS:
            voucher = db.scalar(select(Voucher).where(Voucher.code == data["code"]))
            if voucher is None:
                voucher = Voucher(code=data["code"])
                db.add(voucher)
                created += 1
            for key, value in data.items():
                setattr(voucher, key, value)
            voucher.is_active = True
        db.commit()
    return created


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Đã thêm {seed()} voucher mới, tổng {len(VOUCHERS)} voucher mẫu.")
