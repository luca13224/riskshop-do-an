"""Test lớp 1 — điểm tin cậy tài khoản (Trust Score, bộ luật v3) và túi voucher.

Thiết kế: docs/reviews/2026-10-31_TRUST_SCORE_DESIGN.md.
"""

import uuid
from datetime import timedelta

from sqlalchemy import select

from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.order.models import COD, DELIVERED, PREPAID, Address, Order
from app.modules.promotion.models import PERCENT, Voucher
from app.modules.risk.models import PLACE_ORDER, VOUCHER_APPLY, PAYMENT_OPTIONS
from app.modules.risk.seed import POLICIES
from app.modules.risk.service import decide, trust_tier
from tests.test_risk_scenarios import (  # noqa: F401  (fixture shop dùng chung)
    ADDRESS, browse, checkout, customer, hit_codes, last_decision, shop,
)


# ---------- Hàm thuần: bậc và ma trận ----------

def test_trust_tiers():
    assert [trust_tier(s) for s in (100, 70, 69, 50, 49, 30, 29, 1, 0, -40)] == [
        "normal", "normal", "watch", "watch", "restricted", "restricted", "review", "review", "critical", "critical"]


def test_voucher_locked_below_its_min_trust():
    th = POLICIES[VOUCHER_APPLY]
    # Điểm voucher thấp (không vượt ngưỡng cũ) nhưng tin cậy 60 < 70 của GIAM10 -> gỡ mã
    decision, actions = decide(VOUCHER_APPLY, {"voucher": 10}, {}, th, trust=60, voucher_min_trust=70)
    assert decision == "ALLOW_WITH_RESTRICTION" and actions["remove_voucher"]
    # Cùng điểm tin cậy nhưng mã yêu cầu 50 (NGUOIMOI) -> vẫn dùng được
    decision, actions = decide(VOUCHER_APPLY, {"voucher": 10}, {}, th, trust=60, voucher_min_trust=50)
    assert decision == "ALLOW" and not actions["remove_voucher"]
    # Khiếu nại được chấp nhận (miễn trừ voucher) -> không khóa mã theo tin cậy
    _, actions = decide(VOUCHER_APPLY, {"voucher": 10}, {}, th, frozenset({"voucher"}), trust=20, voucher_min_trust=50)
    assert not actions["remove_voucher"]


def test_low_trust_flags_but_never_holds_or_blocks_alone():
    th = POLICIES[PLACE_ORDER]
    decision, actions = decide(PLACE_ORDER, {"cod": 0}, {}, th, trust=25)
    assert actions["open_case"] and decision == "ALLOW"  # cắm cờ cho analyst, đơn vẫn đi
    decision, actions = decide(PLACE_ORDER, {"cod": 0}, {}, th, trust=-10)
    assert actions["disable_cod"] and decision == "ALLOW_WITH_RESTRICTION"  # tắt COD, vẫn cho trả trước
    assert not actions["hold_order"] and not actions["block"]
    # Bước xem phương thức thanh toán: tắt COD nhưng không mở case (chỉ mở lúc đặt hàng)
    _, actions = decide(PAYMENT_OPTIONS, {"cod": 0}, {}, POLICIES[PAYMENT_OPTIONS], trust=-10)
    assert actions["disable_cod"] and not actions["open_case"]


def test_trust_layer_can_be_switched_off():
    th = {k: v for k, v in POLICIES[PLACE_ORDER].items() if k != "trust"}
    decision, actions = decide(PLACE_ORDER, {"voucher": 0, "cod": 0}, {}, th, trust=-50, voucher_min_trust=70)
    assert decision == "ALLOW" and not any(actions.values())


# ---------- Qua API thật ----------

def test_trust_recorded_with_deductions(shop, db):
    c = customer("moi@example.com", "device-moi-0001")
    browse(c)  # không xem sản phẩm thì R06 "tốc độ giống bot" cũng trừ điểm
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    d = last_decision(db, "moi@example.com")
    assert d.features_snapshot["trust_score"] == 90  # 100 - R01 (tài khoản mới dùng mã người mới)
    assert d.features_snapshot["trust_deductions"] == {"VCH_NEW_ACCOUNT": 10}
    assert d.features_snapshot["trust_tier"] == "normal"


def test_phone_shared_across_addresses_is_deducted(shop, db):
    # Một SĐT nhận hàng cho 3 tài khoản ở 3 địa chỉ khác nhau (farm chia điểm nhận, một người đi nhận)
    for i in range(1, 4):
        c = customer(f"drop{i}@example.com", f"device-drop-{i:04d}", ip=f"192.0.2.{120 + i}")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        addr = {**ADDRESS, "line": f"{i * 10} Đường Thử {i}", "phone": "0987000111"}
        r = c.post("/api/orders/checkout", json={"address": addr, "payment_method": PREPAID},
                   headers={"Idempotency-Key": str(uuid.uuid4())})
        assert r.status_code == 201
    d = last_decision(db, "drop3@example.com")
    assert d.features_snapshot["accounts_on_phone_30d"] == 3
    assert d.features_snapshot["addresses_on_phone_30d"] == 3
    # Đơn trả trước không dùng mã: lớp 2 (chính sách voucher) không chạy, nhưng lớp 1 vẫn trừ điểm tin cậy
    assert "PHONE_MULTI_ACCOUNTS" not in hit_codes(db, d)
    assert d.features_snapshot["trust_deductions"]["PHONE_MULTI_ACCOUNTS"] == 15


def _history_with_vouchers(db, email: str, orders: int, discount: int, subtotal: int = 300_000):
    db.rollback()  # bỏ "ảnh chụp" cũ của transaction để thấy tài khoản vừa đăng ký qua API
    user = db.scalar(select(User).where(User.email == email))
    user.created_at = utcnow() - timedelta(days=60)
    addr = Address(user_id=user.id, recipient_name="X", phone="0900000000", line="1 A", ward="B", district="C",
                   province="D", norm_hash=uuid.uuid4().hex + uuid.uuid4().hex, created_at=user.created_at)
    db.add(addr)
    db.flush()
    for i in range(orders):
        db.add(Order(order_code=f"V{user.id}X{i}", user_id=user.id, address_id=addr.id, status=DELIVERED,
                     payment_method=COD, payment_status="PAID", subtotal=subtotal, discount=discount,
                     total=subtotal - discount, idempotency_key=uuid.uuid4().hex,
                     created_at=utcnow() - timedelta(days=20 - i)))
    db.commit()


def test_high_voucher_subsidy_deducts_and_profitable_customer_recovers(shop, db):
    db.add(Voucher(code="GIAM10", discount_type=PERCENT, amount=10, max_discount=100_000, min_order_value=0,
                   risk_checked=True, min_trust=70))
    db.commit()
    san = customer("sansale@example.com", "device-sale-0001")
    _history_with_vouchers(db, "sansale@example.com", orders=4, discount=90_000)  # sàn bù 30%
    san.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    san.post("/api/cart/voucher", json={"code": "GIAM10"})
    d = last_decision(db, "sansale@example.com")
    assert d.features_snapshot["voucher_subsidy_ratio_90d"] == 0.3
    assert d.features_snapshot["trust_deductions"].get("VOUCHER_SUBSIDY_HIGH") == 20

    deu = customer("muadeu@example.com", "device-deu-0001")
    _history_with_vouchers(db, "muadeu@example.com", orders=4, discount=0)  # mua đều, không dùng mã
    deu.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    deu.post("/api/cart/voucher", json={"code": "GIAM10"})
    d = last_decision(db, "muadeu@example.com")
    assert d.features_snapshot["trust_deductions"].get("PROFITABLE_CUSTOMER") == -15
    assert d.features_snapshot["trust_score"] == 100  # luật tích cực cộng lại, tối đa 100


def test_wallet_grants_welcome_voucher_and_locks_when_trust_drops(shop, db):
    db.query(Voucher).filter(Voucher.code == "NGUOIMOI").update({"min_trust": 50})
    db.commit()
    # Đăng ký xong là có NGUOIMOI trong túi
    ok = customer("vi@example.com", "device-vi-0001")
    wallet = ok.get("/api/vouchers/wallet").json()
    assert [(w["code"], w["status"], w["granted"]) for w in wallet] == [("NGUOIMOI", "usable", True)]
    assert "trust" not in str(wallet).lower()  # không lộ điểm tin cậy cho khách

    # Farm: tài khoản thứ 3 trên cùng máy -> R01 + R02 + R04 + R06 (không xem sản phẩm) = 75 -> tin cậy 25 < 50
    for i in range(1, 4):
        c = customer(f"vifarm{i}@example.com", "device-vifarm-01")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    assert last_decision(db, "vifarm3@example.com").features_snapshot["trust_score"] == 25
    assert c.get("/api/vouchers/wallet").json()[0]["status"] == "locked"


def test_staff_cannot_read_customer_wallet(shop, client):
    assert client.get("/api/vouchers/wallet").status_code == 401
