"""Test đặt hàng: transaction, idempotency, tồn kho, voucher, chống race condition, giao hàng."""

import threading
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import ADMIN, ANALYST
from app.modules.catalog.models import Product
from app.modules.order.schemas import AddressIn
from app.modules.order.service import normalize_address
from app.modules.promotion.models import FIXED, Voucher, VoucherRedemption

ADDRESS = {
    "recipient_name": "Nguyễn Minh",
    "phone": "0901234567",
    "line": "Số 05 Nguyễn Trãi",
    "ward": "Phường Bến Thành",
    "district": "Quận 1",
    "province": "TP Hồ Chí Minh",
}


@pytest.fixture
def shop(db):
    db.add_all(
        [
            Product(id=1, sku="P-1", slug="p1", name="Tai nghe", category="audio", price=300_000, stock=5),
            Product(id=2, sku="P-2", slug="p2", name="Món cuối", category="gear", price=250_000, stock=1),
            Voucher(id=1, code="NGUOIMOI", discount_type=FIXED, amount=50_000, min_order_value=200_000),
            Voucher(id=2, code="CUOICUNG", discount_type=FIXED, amount=10_000, max_redemptions=1),
        ]
    )
    db.commit()


def new_customer(email: str) -> TestClient:
    c = TestClient(app)
    resp = c.post(
        "/api/auth/register",
        json={"email": email, "password": "matkhau123", "full_name": "Khách"},
        headers={"X-Device-Id": f"device-{uuid.uuid4()}"},
    )
    assert resp.status_code == 201
    return c


def checkout(c: TestClient, key: str | None = None, method: str = "COD"):
    return c.post(
        "/api/orders/checkout",
        json={"address": ADDRESS, "payment_method": method},
        headers={"Idempotency-Key": key or str(uuid.uuid4())},
    )


@pytest.fixture
def minh(shop):
    return new_customer("minh@example.com")


# ---------- Đặt hàng cơ bản ----------

def test_checkout_creates_order_and_clears_cart(minh, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 2})
    minh.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    resp = checkout(minh)
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "CONFIRMED" and order["payment_status"] == "UNPAID"
    assert order["subtotal"] == 600_000 and order["discount"] == 50_000 and order["total"] == 550_000
    assert order["items"][0]["unit_price"] == 300_000 and order["voucher_code"] == "NGUOIMOI"
    assert minh.get("/api/cart").json()["items"] == []
    assert db.get(Product, 1).stock == 3
    assert db.get(Voucher, 1).redeemed_count == 1


def test_prepaid_is_marked_paid(minh):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert checkout(minh, method="PREPAID").json()["payment_status"] == "PAID"


def test_price_is_snapshotted(minh, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    code = checkout(minh).json()["order_code"]
    db.query(Product).filter(Product.id == 1).update({Product.price: 999_000})
    db.commit()
    assert minh.get(f"/api/orders/{code}").json()["items"][0]["unit_price"] == 300_000


def test_empty_cart_and_missing_key(minh):
    assert checkout(minh).json()["error"]["code"] == "CART_EMPTY"
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    resp = minh.post("/api/orders/checkout", json={"address": ADDRESS, "payment_method": "COD"})
    assert resp.status_code == 400 and resp.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_invalid_address(minh):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    resp = minh.post(
        "/api/orders/checkout",
        json={"address": {**ADDRESS, "phone": "123"}, "payment_method": "COD"},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert resp.status_code == 422


# ---------- Idempotency ----------

def test_same_idempotency_key_returns_same_order(minh, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    key = str(uuid.uuid4())
    first = checkout(minh, key)
    second = checkout(minh, key)  # bấm 2 lần / mạng gửi lại
    assert first.status_code == 201 and second.status_code == 200
    assert first.json()["order_code"] == second.json()["order_code"]
    assert len(minh.get("/api/orders").json()) == 1
    assert db.get(Product, 1).stock == 4  # chỉ trừ kho một lần


# ---------- Rollback khi lỗi ----------

def test_failed_checkout_changes_nothing(minh, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 2})
    minh.post("/api/cart/items", json={"product_id": 2, "quantity": 1})
    db.query(Product).filter(Product.id == 2).update({Product.stock: 0})  # món 2 vừa hết hàng
    db.commit()
    resp = checkout(minh)
    assert resp.json()["error"]["code"] == "NOT_ENOUGH_STOCK"
    db.expire_all()
    assert db.get(Product, 1).stock == 5  # món 1 không bị trừ oan
    assert len(minh.get("/api/cart").json()["items"]) == 2  # giỏ còn nguyên
    assert minh.get("/api/orders").json() == []


def test_voucher_once_per_user(minh):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    minh.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    checkout(minh)
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert minh.post("/api/cart/voucher", json={"code": "NGUOIMOI"}).json()["error"]["code"] == "VOUCHER_ALREADY_USED"


# ---------- Race condition: hai khách đặt hàng CÙNG LÚC ----------

def _race(clients: list[TestClient]) -> list[int]:
    barrier = threading.Barrier(len(clients))
    results: list[int] = []
    lock = threading.Lock()

    def run(c: TestClient):
        barrier.wait()  # cùng xuất phát
        status = checkout(c).status_code
        with lock:
            results.append(status)

    threads = [threading.Thread(target=run, args=(c,)) for c in clients]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(results)


def test_race_last_item_sold_once(shop, db):
    a, b = new_customer("a@example.com"), new_customer("b@example.com")
    for c in (a, b):
        c.post("/api/cart/items", json={"product_id": 2, "quantity": 1})
    assert _race([a, b]) == [201, 409]
    db.expire_all()
    assert db.get(Product, 2).stock == 0  # không bao giờ âm


def test_race_last_voucher_redemption(shop, db):
    a, b = new_customer("a@example.com"), new_customer("b@example.com")
    for c in (a, b):
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        assert c.post("/api/cart/voucher", json={"code": "CUOICUNG"}).status_code == 200
    assert _race([a, b]) == [201, 409]
    db.expire_all()
    assert db.get(Voucher, 2).redeemed_count == 1
    assert db.scalar(select(func.count()).select_from(VoucherRedemption)) == 1


# ---------- Quyền xem đơn ----------

def test_cannot_see_other_customers_order(minh, shop):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    code = checkout(minh).json()["order_code"]
    other = new_customer("khac@example.com")
    assert other.get(f"/api/orders/{code}").status_code == 404


# ---------- Giao hàng (giả lập) ----------

@pytest.fixture
def admin(db):
    auth_service.create_user(db, email="admin@riskshop.test", password="matkhau123", full_name="Admin", role=ADMIN)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "admin@riskshop.test", "password": "matkhau123"})
    return c


def ship(c, code, status):
    return c.post(f"/api/console/orders/{code}/shipment", json={"status": status})


def test_shipment_flow_cod_delivered_marks_paid(minh, admin):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    code = checkout(minh).json()["order_code"]
    assert ship(admin, code, "DELIVERED").json()["error"]["code"] == "INVALID_TRANSITION"
    assert ship(admin, code, "SHIPPING").status_code == 200
    assert ship(admin, code, "DELIVERED").json()["status"] == "DELIVERED"
    order = minh.get(f"/api/orders/{code}").json()
    assert order["payment_status"] == "PAID"
    assert [e["status"] for e in order["events"]] == ["SHIPPING", "DELIVERED"]


def test_delivery_failed_restocks(minh, admin, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 2})
    code = checkout(minh).json()["order_code"]
    ship(admin, code, "SHIPPING")
    ship(admin, code, "DELIVERY_FAILED")
    db.expire_all()
    assert db.get(Product, 1).stock == 5


def test_analyst_cannot_update_shipment(minh, db):
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    code = checkout(minh).json()["order_code"]
    auth_service.create_user(db, email="an@riskshop.test", password="matkhau123", full_name="An", role=ANALYST)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "an@riskshop.test", "password": "matkhau123"})
    assert c.get("/api/console/orders").status_code == 200  # xem được
    assert ship(c, code, "SHIPPING").status_code == 403  # không được sửa


# ---------- Chuẩn hóa địa chỉ (cho luật R03) ----------

def test_address_normalization_matches_variants():
    a = AddressIn(**ADDRESS)
    b = AddressIn(**{**ADDRESS, "line": "so 5 nguyen trai", "ward": "P. Ben Thanh", "district": "Q1",
                     "province": "Hồ Chí Minh"})
    assert normalize_address(a) == normalize_address(b)


@pytest.mark.parametrize("line, province", [
    ("Số 5 ng. 12 Láng Hạ", "HN"),
    ("so 05 ngo 12 lang ha", "Thành phố Hà Nội"),
    ("5 Ng12 Láng Hạ", "ha noi"),
])
def test_address_normalization_lane_and_province_aliases(line, province):
    base = AddressIn(**{**ADDRESS, "line": "Số 5 Ngõ 12 Láng Hạ", "province": "Hà Nội"})
    assert normalize_address(AddressIn(**{**ADDRESS, "line": line, "province": province})) == normalize_address(base)


def test_address_normalization_keeps_different_houses_apart():
    a = AddressIn(**{**ADDRESS, "line": "12/5 Nguyễn Trãi"})
    b = AddressIn(**{**ADDRESS, "line": "5/12 Nguyễn Trãi"})
    assert normalize_address(a) != normalize_address(b)  # không đoán thứ tự số nhà / số hẻm
    hcm = AddressIn(**{**ADDRESS, "province": "TP.HCM"})
    assert normalize_address(hcm) == normalize_address(AddressIn(**{**ADDRESS, "province": "Sài Gòn"}))
    # "dn" trong tên đường không bị đổi thành Đà Nẵng
    assert "dn" in normalize_address(AddressIn(**{**ADDRESS, "line": "Kho DN 3"}))


def test_console_orders_filter_search_and_paginate(minh, admin, shop):
    codes = []
    for _ in range(3):
        minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        codes.append(checkout(minh).json()["order_code"])
    ship(admin, codes[0], "SHIPPING")

    body = admin.get("/api/console/orders").json()
    assert body["total"] == 3 and body["status_counts"] == {"CONFIRMED": 2, "SHIPPING": 1}
    assert [o["order_code"] for o in body["items"]] == codes[::-1]  # mới nhất trước

    shipping = admin.get("/api/console/orders", params={"status": "SHIPPING"}).json()
    assert [o["order_code"] for o in shipping["items"]] == [codes[0]]
    assert shipping["status_counts"]["CONFIRMED"] == 2  # chip vẫn hiện số của trạng thái khác

    found = admin.get("/api/console/orders", params={"q": codes[1]}).json()
    assert [o["order_code"] for o in found["items"]] == [codes[1]]
    assert admin.get("/api/console/orders", params={"q": "khong-ton-tai"}).json()["total"] == 0

    page2 = admin.get("/api/console/orders", params={"page": 2, "page_size": 2}).json()
    assert [o["order_code"] for o in page2["items"]] == [codes[0]]


def test_console_orders_rejects_bad_status_and_customers(minh, admin):
    assert admin.get("/api/console/orders", params={"status": "HACKED"}).status_code == 422
    assert minh.get("/api/console/orders").status_code == 403
