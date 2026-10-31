"""Tái hiện các nhân vật trong kịch bản demo (DEMO_SCRIPT.md, RULES_V0.md mục 5) qua API thật."""

import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.time import utcnow
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import ANALYST, User
from app.modules.catalog.models import Product
from app.modules.order.models import COD, DELIVERED, DELIVERY_FAILED, PREPAID, Address, Order
from app.modules.promotion.models import FIXED, Voucher
from app.modules.risk import features as feature_store
from app.modules.risk.models import RiskDecision, RuleHit
from app.modules.risk.seed import seed_rules

ADDRESS = {"recipient_name": "Khách", "phone": "0901234567", "line": "12 Láng Hạ",
           "ward": "Thành Công", "district": "Ba Đình", "province": "Hà Nội"}


@pytest.fixture
def shop(db):
    seed_rules(db)
    db.add_all([
        Product(id=1, sku="P-1", slug="tai-nghe", name="Tai nghe", category="audio", price=300_000, stock=100),
        Product(id=2, sku="P-2", slug="loa", name="Loa", category="audio", price=3_500_000, stock=100),
        Product(id=3, sku="P-3", slug="man-hinh", name="Màn hình", category="monitor", price=5_490_000, stock=100),
        Voucher(code="NGUOIMOI", discount_type=FIXED, amount=50_000, min_order_value=200_000,
                new_user_only=True, risk_checked=True),
    ])
    db.commit()


def customer(email: str, device: str, ip: str = "203.0.113.10") -> TestClient:
    c = TestClient(app, client=(ip, 50000))
    c.headers["X-Device-Id"] = device
    r = c.post("/api/auth/register", json={"email": email, "password": "matkhau123", "full_name": email.split("@")[0]})
    assert r.status_code == 201, r.text
    return c


def browse(c: TestClient, slug: str = "tai-nghe") -> None:
    assert c.get(f"/api/products/{slug}").status_code == 200  # người thật xem sản phẩm trước khi mua


def checkout(c: TestClient, method: str = COD):
    return c.post("/api/orders/checkout", json={"address": ADDRESS, "payment_method": method},
                  headers={"Idempotency-Key": str(uuid.uuid4())})


def last_decision(db, email: str) -> RiskDecision:
    # Kết thúc transaction đang mở: với REPEATABLE READ (mặc định của MariaDB), session đã đọc
    # trước đó sẽ chỉ thấy "ảnh chụp" cũ và không thấy quyết định mới do request khác ghi.
    db.rollback()
    user_id = db.scalar(select(User.id).where(User.email == email))
    return db.scalar(select(RiskDecision).where(RiskDecision.user_id == user_id).order_by(RiskDecision.id.desc()))


def hit_codes(db, decision: RiskDecision) -> set[str]:
    return set(db.scalars(select(RuleHit.rule_code).where(RuleHit.decision_id == decision.id)))


def add_history(db, email: str, *, cod_delivered=0, cod_failed=0, days_old=90) -> None:
    """Tạo lịch sử đơn hàng đã kết thúc trong quá khứ cho một khách."""
    user = db.scalar(select(User).where(User.email == email))
    user.created_at = utcnow() - timedelta(days=days_old)
    addr = Address(user_id=user.id, recipient_name="X", phone="0900000000", line="1 A", ward="B", district="C",
                   province="D", norm_hash=uuid.uuid4().hex + uuid.uuid4().hex, created_at=user.created_at)
    db.add(addr)
    db.flush()
    statuses = [DELIVERED] * cod_delivered + [DELIVERY_FAILED] * cod_failed
    for i, status in enumerate(statuses):
        db.add(Order(order_code=f"H{user.id}X{i}", user_id=user.id, address_id=addr.id, status=status,
                     payment_method=COD, payment_status="PAID", subtotal=300_000, total=300_000,
                     idempotency_key=uuid.uuid4().hex, created_at=user.created_at + timedelta(days=1)))
    db.commit()


# ---------- Cảnh 1: khách mới hợp lệ ----------

def test_new_customer_voucher_allowed(shop, db):
    minh = customer("minh@example.com", "device-minh-0001")
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    r = minh.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    assert r.status_code == 200 and r.json()["voucher"]["code"] == "NGUOIMOI"
    d = last_decision(db, "minh@example.com")
    assert d.decision == "ALLOW" and d.score == 10 and hit_codes(db, d) == {"VCH_NEW_ACCOUNT"}


# ---------- Cảnh 2: farm voucher (một thiết bị, nhiều tài khoản mới) ----------

def test_voucher_farm_on_one_device_is_restricted(shop, db):
    results = []
    for i in range(1, 4):
        c = customer(f"farm{i}@example.com", "device-farm-0001")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        results.append(c.post("/api/cart/voucher", json={"code": "NGUOIMOI"}))
    assert [r.status_code for r in results] == [200, 200, 409]
    err = results[2].json()["error"]
    assert err["code"] == "VOUCHER_NOT_APPLICABLE"
    assert "thiết bị" not in err["message"]  # không lộ luật cho khách
    d = last_decision(db, "farm3@example.com")
    assert d.decision == "ALLOW_WITH_RESTRICTION" and d.score == 55  # 10 + 35 + 10
    assert hit_codes(db, d) == {"VCH_NEW_ACCOUNT", "DEV_MULTI_NEW_ACCOUNTS", "IP_MULTI_NEW_ACCOUNTS"}


# ---------- Cảnh 4: gia đình chung Wi-Fi và địa chỉ (hard negative) ----------

def test_family_sharing_wifi_and_address_is_allowed(shop, db):
    for i in range(1, 5):
        c = customer(f"giadinh{i}@example.com", f"device-giadinh-{i:04d}", ip="198.51.100.7")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        assert c.post("/api/cart/voucher", json={"code": "NGUOIMOI"}).status_code == 200
        assert checkout(c, PREPAID).status_code == 201
    d = last_decision(db, "giadinh4@example.com")
    # Người thứ 4: R01 (+10) + R04 cùng IP (+10) + R03 cùng địa chỉ (+20) = 40 < 50
    assert d.context == "place_order" and d.decision == "ALLOW" and d.score == 40
    assert hit_codes(db, d) == {"VCH_NEW_ACCOUNT", "IP_MULTI_NEW_ACCOUNTS", "ADDR_MULTI_ACCOUNTS"}


# ---------- Bộ luật v2: farm phân tán (mỗi tài khoản một máy, một mạng, cùng một nhà) ----------

def spread_member(i: int) -> TestClient:
    c = customer(f"spread{i}@example.com", f"device-spread-{i:04d}", ip=f"192.0.2.{10 + i}")
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert c.post("/api/cart/voucher", json={"code": "NGUOIMOI"}).status_code == 200  # lúc áp mã chưa có địa chỉ
    return c


def test_spread_farm_caught_from_fifth_account(shop, db):
    for i in range(1, 5):
        assert checkout(spread_member(i), PREPAID).status_code == 201
    d4 = last_decision(db, "spread4@example.com")
    # Thứ 4: chưa đủ ngưỡng cụm (F12 = 4 < 5) -> chỉ R01 + R03 bậc 3 = 30, vẫn cho phép
    assert d4.decision == "ALLOW" and "ADDR_VOUCHER_RING" not in hit_codes(db, d4)

    r = checkout(spread_member(5), PREPAID)
    assert r.status_code == 409 and r.json()["error"]["code"] == "VOUCHER_NOT_APPLICABLE"
    assert "địa chỉ" not in r.json()["error"]["message"]  # không lộ luật cho khách
    d5 = last_decision(db, "spread5@example.com")
    assert d5.features_snapshot["new_accounts_on_address_7d"] == 5
    assert d5.features_snapshot["address_ip_diversity_7d"] == 1.0
    # R01 (+10) + R03 bậc 5 (+30) + R11 (+25) = 65 >= 50 -> gỡ voucher (v1 chỉ có 40, lọt)
    assert d5.decision == "ALLOW_WITH_RESTRICTION" and d5.score == 65
    assert hit_codes(db, d5) == {"VCH_NEW_ACCOUNT", "ADDR_MULTI_ACCOUNTS", "ADDR_VOUCHER_RING"}


def test_spread_rule_ignores_orders_without_new_user_voucher(shop, db):
    for i in range(1, 6):
        c = customer(f"noncoupon{i}@example.com", f"device-nc-{i:04d}", ip=f"192.0.2.{50 + i}")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        assert checkout(c, PREPAID).status_code == 201
    d = last_decision(db, "noncoupon5@example.com")
    assert d.features_snapshot["new_accounts_on_address_7d"] == 5
    assert "ADDR_VOUCHER_RING" not in hit_codes(db, d)


def test_family_low_network_diversity_not_hit_by_spread_rule(shop, db):
    for i in range(1, 6):
        c = customer(f"nha{i}@example.com", f"device-nha-{i:04d}", ip="198.51.100.9")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
        # Người 1–4 đặt được; người thứ 5 bị gỡ voucher (409) bởi luật v1, không phải R11
        assert checkout(c, PREPAID).status_code == (201 if i < 5 else 409)
    d = last_decision(db, "nha5@example.com")
    assert d.features_snapshot["address_ip_diversity_7d"] == 0.2  # 1 mạng / 5 tài khoản
    # R11 không khớp. (Người thứ 5 vẫn bị gỡ voucher do R01+R03+R04 = 50: giới hạn đã biết của v1, không đổi.)
    assert "ADDR_VOUCHER_RING" not in hit_codes(db, d)


# ---------- Cảnh 5: COD ----------

def test_khang_cod_hidden_and_rejected_but_prepaid_ok(shop, db):
    khang = customer("khang@example.com", "device-khang-0001")
    add_history(db, "khang@example.com", cod_delivered=1, cod_failed=4)
    browse(khang)
    khang.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert khang.get("/api/orders/payment-options").json() == {
        "cod_allowed": False, "message": "Đơn hàng này hỗ trợ thanh toán trước."}
    r = checkout(khang, COD)  # kể cả gọi thẳng API với COD, server vẫn chặn
    assert r.status_code == 409 and r.json()["error"]["code"] == "COD_NOT_AVAILABLE"
    assert "COD_FAIL_RATE" in hit_codes(db, last_decision(db, "khang@example.com"))
    assert checkout(khang, PREPAID).status_code == 201


def test_new_account_high_value_cod_goes_to_review(shop, db):
    c = customer("moi@example.com", "device-moi-0001")
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    r = checkout(c, COD)
    assert r.status_code == 201 and r.json()["status"] == "PENDING_REVIEW"
    d = last_decision(db, "moi@example.com")
    assert d.decision == "REVIEW" and d.order_id is not None and d.actions["open_case"]
    assert "COD_HIGH_VALUE_LOW_HISTORY" in hit_codes(db, d)


def test_new_account_mid_value_cod_must_prepay(shop, db):
    c = customer("vua@example.com", "device-vua-0001")
    browse(c, "loa")
    c.post("/api/cart/items", json={"product_id": 2, "quantity": 1})
    # Giao diện và lúc đặt hàng phải NHẤT QUÁN: đã báo không có COD thì đặt COD cũng bị từ chối
    assert c.get("/api/orders/payment-options").json()["cod_allowed"] is False
    assert checkout(c, COD).json()["error"]["code"] == "COD_NOT_AVAILABLE"  # R08 bậc 3 triệu: +40


def test_review_case_still_offers_cod(shop, db):
    c = customer("moi2@example.com", "device-moi2-0001")
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    # Đơn này sẽ được GIỮ chờ duyệt chứ không bị cấm COD, nên vẫn hiện lựa chọn COD
    assert c.get("/api/orders/payment-options").json()["cod_allowed"] is True
    assert checkout(c, COD).json()["status"] == "PENDING_REVIEW"


def test_seed_creates_new_version_instead_of_overwriting(shop, db):
    from app.modules.risk.models import Rule, RuleVersion
    rule = db.scalar(select(Rule).where(Rule.code == "VCH_VELOCITY"))
    v1 = db.get(RuleVersion, rule.active_version_id)
    v1.params = {**v1.params, "tiers": [{"gte": 9, "points": 25}]}  # giả lập bản đang dùng khác với file seed
    db.commit()
    assert seed_rules(db) == 1
    db.refresh(rule)
    versions = db.scalars(select(RuleVersion).where(RuleVersion.rule_id == rule.id)).all()
    assert len(versions) == 2 and db.get(RuleVersion, rule.active_version_id).version == 2


def test_loyal_customer_high_value_cod_allowed(shop, db):
    lan = customer("lan@example.com", "device-lan-0001")
    add_history(db, "lan@example.com", cod_delivered=30)
    lan.post("/api/cart/items", json={"product_id": 2, "quantity": 1})
    r = checkout(lan, COD)
    assert r.status_code == 201 and r.json()["status"] == "CONFIRMED"
    d = last_decision(db, "lan@example.com")
    assert d.decision == "ALLOW" and "GOOD_HISTORY" in hit_codes(db, d)


def test_bot_speed_signal(shop, db):
    c = customer("bot@example.com", "device-bot-0001")  # không xem sản phẩm nào, đặt ngay
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    checkout(c, PREPAID)
    assert "BOT_SPEED" not in hit_codes(db, last_decision(db, "bot@example.com"))  # trả trước, không voucher
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    checkout(c, COD)
    d = last_decision(db, "bot@example.com")
    assert "BOT_SPEED" in hit_codes(db, d), (d.context, d.decision, d.policy_scores, d.features_snapshot)


# ---------- An toàn khi Risk Engine lỗi ----------

def test_engine_failure_fail_open_for_voucher(shop, db, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("feature store down")

    monkeypatch.setattr(feature_store, "compute", broken)
    c = customer("loi@example.com", "device-loi-0001")
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert c.post("/api/cart/voucher", json={"code": "NGUOIMOI"}).status_code == 200  # fail-open
    d = last_decision(db, "loi@example.com")
    assert d.decision == "ALLOW" and "feature store down" in d.error


def test_engine_failure_fail_closed_for_high_value_cod(shop, db, monkeypatch):
    c = customer("loi2@example.com", "device-loi2-0001")
    c.post("/api/cart/items", json={"product_id": 2, "quantity": 1})
    monkeypatch.setattr(feature_store, "compute", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down")))
    assert checkout(c, COD).json()["error"]["code"] == "COD_NOT_AVAILABLE"  # fail-closed


# ---------- Console ----------

def test_console_lists_decisions_with_reasons(shop, db):
    c = customer("minh@example.com", "device-minh-0001")
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    assert c.get("/api/console/risk/decisions").status_code == 403  # khách không xem được

    auth_service.create_user(db, email="an@riskshop.test", password="matkhau123", full_name="An", role=ANALYST)
    staff = TestClient(app)
    staff.post("/api/auth/login", json={"email": "an@riskshop.test", "password": "matkhau123"})
    items = staff.get("/api/console/risk/decisions").json()
    assert items[0]["user_email"] == "mi***@example.com"  # Console chỉ thấy email đã che
    assert items[0]["hits"][0]["reason_text"].startswith("Tài khoản mới tạo")
