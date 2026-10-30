"""Demo reset: đưa CSDL về trạng thái chuẩn cho buổi demo / mỗi đợt đo (DEMO_SCRIPT.md, "Yêu cầu riêng cho buổi demo").

    python -m app.modules.lab.reset --yes

XÓA TOÀN BỘ dữ liệu rồi tạo lại: sản phẩm, voucher, bộ luật v1, nhân viên và các nhân vật của kịch bản demo.
Chỉ chạy khi DEMO_MODE=true. Mật khẩu sinh ngẫu nhiên, ghi vào backend/.env.accounts (không commit).

Nhân vật:
- Minh: khách mới hợp lệ, đăng ký hôm qua (cảnh 1: dùng TANTHU được).
- Khang: khách cũ, 5 đơn COD trong quá khứ, 4 đơn giao thất bại (cảnh 5a: không được COD).
- Lan: khách thân thiết, 30 đơn giao thành công (cảnh 5c: COD giá trị cao vẫn được).
- analyst / manager / admin: nhân viên các vai trò.
"""

import argparse
import hashlib
import secrets
import sys
import time
import uuid
from datetime import timedelta
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (nạp đủ model để biết mọi bảng)
from app.core.config import BACKEND_DIR, get_settings
from app.core.db import Base, SessionLocal
from app.core.time import utcnow
from app.modules.auth import security
from app.modules.auth.models import ADMIN, ANALYST, CUSTOMER, RISK_MANAGER, User
from app.modules.catalog import seed as catalog_seed
from app.modules.catalog.models import Product
from app.modules.order.models import COD, DELIVERED, DELIVERY_FAILED, Address, Order, OrderItem, ShipmentEvent
from app.modules.promotion import seed as promotion_seed
from app.modules.risk.seed import seed_rules

ACCOUNTS_FILE = BACKEND_DIR / ".env.accounts"

STAFF = [
    ("analyst@riskshop.test", "Analyst Demo", ANALYST),
    ("manager@riskshop.test", "Risk Manager Demo", RISK_MANAGER),
    ("admin@riskshop.test", "Admin Demo", ADMIN),
]


def _wipe(db: Session) -> None:
    db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for table in Base.metadata.sorted_tables:
        db.execute(text(f"TRUNCATE TABLE `{table.name}`"))
    db.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    db.commit()


def make_user(db: Session, email: str, name: str, role: str, password: str, age: timedelta, phone: str | None = None):
    user = User(email=email, full_name=name, role=role, phone=phone,
                password_hash=security.hash_password(password), created_at=utcnow() - age)
    db.add(user)
    db.flush()
    return user


def add_history(db: Session, user: User, product: Product, outcomes: list[str]) -> None:
    """Tạo lịch sử đơn COD đã kết thúc trong quá khứ (dữ liệu seed, ghi rõ là mô phỏng)."""
    line = f"{secrets.randbelow(300) + 1} Đường Demo {user.id}"
    norm = hashlib.sha256(f"seed-address-{user.id}".encode()).hexdigest()
    addr = Address(user_id=user.id, recipient_name=user.full_name, phone=user.phone or "0900000000", line=line,
                   ward="Phường Demo", district="Quận Demo", province="Hà Nội", norm_hash=norm,
                   created_at=user.created_at)
    db.add(addr)
    db.flush()
    for i, outcome in enumerate(outcomes):
        placed = user.created_at + timedelta(days=3 + i * 2)
        order = Order(order_code=f"RSSEED{user.id:02d}{i:03d}", user_id=user.id, address_id=addr.id, status=outcome,
                      payment_method=COD, payment_status="PAID" if outcome == DELIVERED else "UNPAID",
                      subtotal=product.price, discount=0, total=product.price,
                      idempotency_key=uuid.uuid4().hex, created_at=placed, updated_at=placed + timedelta(days=2))
        db.add(order)
        db.flush()
        db.add(OrderItem(order_id=order.id, product_id=product.id, product_name=product.name,
                         category=product.category, unit_price=product.price, quantity=1))
        db.add(ShipmentEvent(order_id=order.id, status="SHIPPING", note="Dữ liệu seed",
                             occurred_at=placed + timedelta(days=1)))
        db.add(ShipmentEvent(order_id=order.id, status=outcome, note="Dữ liệu seed",
                             occurred_at=placed + timedelta(days=2)))


def reset(db: Session) -> dict[str, str]:
    """Xóa sạch và tạo lại dữ liệu demo. Trả về {email: mật khẩu}."""
    _wipe(db)
    catalog_seed.seed(db)
    promotion_seed.seed(db)
    seed_rules(db)

    credentials: dict[str, str] = {}

    def password_for(email: str) -> str:
        credentials[email] = secrets.token_urlsafe(9)
        return credentials[email]

    for email, name, role in STAFF:
        make_user(db, email, name, role, password_for(email), timedelta(days=60))

    cheap = db.query(Product).filter(Product.sku == "SM-002").one()  # Ổ cắm thông minh (món rẻ)
    make_user(db, "minh@shop.test", "Nguyễn Minh", CUSTOMER, password_for("minh@shop.test"), timedelta(hours=20),
          phone="0901111111")
    khang = make_user(db, "khang@shop.test", "Phạm Khang", CUSTOMER, password_for("khang@shop.test"),
                  timedelta(days=90), phone="0902222222")
    add_history(db, khang, cheap, [DELIVERED] + [DELIVERY_FAILED] * 4)
    lan = make_user(db, "lan@shop.test", "Trần Lan", CUSTOMER, password_for("lan@shop.test"), timedelta(days=365),
                phone="0903333333")
    add_history(db, lan, cheap, [DELIVERED] * 30)
    db.commit()
    return credentials


def write_accounts(credentials: dict[str, str], path: Path = ACCOUNTS_FILE) -> None:
    lines = ["# Tài khoản demo (tạo bởi demo reset) — CHỈ dùng local, KHÔNG commit"]
    lines += [f"{email}={password}" for email, password in credentials.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Đưa CSDL về trạng thái chuẩn cho demo (XÓA TOÀN BỘ dữ liệu)")
    parser.add_argument("--yes", action="store_true", help="xác nhận xóa toàn bộ dữ liệu")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.demo_mode:
        print("Từ chối: chỉ chạy khi DEMO_MODE=true (không bao giờ chạy trên hệ thống thật).", file=sys.stderr)
        return 1
    if not args.yes:
        print("Lệnh này XÓA TOÀN BỘ dữ liệu. Chạy lại kèm --yes nếu chắc chắn.", file=sys.stderr)
        return 1
    started = time.perf_counter()
    with SessionLocal() as db:
        credentials = reset(db)
    write_accounts(credentials)
    print(f"Đã reset dữ liệu demo trong {time.perf_counter() - started:.1f} giây.")
    print(f"Tài khoản và mật khẩu: {ACCOUNTS_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
