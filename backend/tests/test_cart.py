"""Test giỏ hàng và điều kiện voucher (luật nghiệp vụ)."""

from datetime import timedelta

import pytest

from app.core.time import utcnow
from app.modules.auth import service as auth_service
from app.modules.auth.models import ANALYST, User
from app.modules.catalog.models import Product
from app.modules.promotion.models import FIXED, PERCENT, Voucher

DEVICE = {"X-Device-Id": "device-cart-0001"}


@pytest.fixture
def shop(db):
    db.add_all(
        [
            Product(id=1, sku="P-1", slug="p1", name="Tai nghe", category="audio", price=150_000, stock=10),
            Product(id=2, sku="P-2", slug="p2", name="Bàn phím", category="monitor", price=400_000, stock=2),
            Product(id=3, sku="P-3", slug="p3", name="Hết hàng", category="gear", price=100_000, stock=0),
            Voucher(code="TANTHU", discount_type=FIXED, amount=50_000, min_order_value=200_000, new_user_only=True),
            Voucher(code="GIAM10", discount_type=PERCENT, amount=10, max_discount=30_000, min_order_value=0),
            Voucher(code="HETHAN", discount_type=FIXED, amount=10_000, ends_at=utcnow() - timedelta(days=1)),
            Voucher(code="HETLUOT", discount_type=FIXED, amount=10_000, max_redemptions=5, redeemed_count=5),
            Voucher(code="TAT", discount_type=FIXED, amount=10_000, is_active=False),
        ]
    )
    db.commit()


@pytest.fixture
def customer(client, shop):
    resp = client.post(
        "/api/auth/register",
        json={"email": "khach@example.com", "password": "matkhau123", "full_name": "Khách"},
        headers=DEVICE,
    )
    assert resp.status_code == 201
    return client


def add(client, product_id, quantity=1):
    return client.post("/api/cart/items", json={"product_id": product_id, "quantity": quantity})


# ---------- Giỏ hàng ----------

def test_cart_requires_login(client, shop):
    assert client.get("/api/cart").status_code == 401


def test_staff_has_no_cart(client, shop, db):
    auth_service.create_user(db, email="a@riskshop.test", password="matkhau123", full_name="A", role=ANALYST)
    client.post("/api/auth/login", json={"email": "a@riskshop.test", "password": "matkhau123"})
    assert client.get("/api/cart").status_code == 403


def test_empty_cart(customer):
    body = customer.get("/api/cart").json()
    assert body["items"] == [] and body["total"] == 0


def test_add_merges_same_product_and_totals(customer):
    add(customer, 1, 2)
    body = add(customer, 1, 1).json()
    assert body["items"][0]["quantity"] == 3
    assert body["subtotal"] == 450_000 and body["total"] == 450_000
    assert body["item_count"] == 3


def test_stock_limits(customer):
    resp = add(customer, 2, 3)
    assert resp.status_code == 409 and resp.json()["error"]["code"] == "NOT_ENOUGH_STOCK"
    assert add(customer, 3).json()["error"]["code"] == "OUT_OF_STOCK"
    add(customer, 2, 2)
    assert add(customer, 2, 1).json()["error"]["code"] == "NOT_ENOUGH_STOCK"


def test_update_and_remove_item(customer):
    add(customer, 1)
    assert customer.patch("/api/cart/items/1", json={"quantity": 4}).json()["subtotal"] == 600_000
    assert customer.patch("/api/cart/items/1", json={"quantity": 0}).status_code == 422
    assert customer.delete("/api/cart/items/1").json()["items"] == []
    assert customer.patch("/api/cart/items/1", json={"quantity": 1}).status_code == 404


def test_unknown_product(customer):
    assert add(customer, 999).status_code == 404


# ---------- Voucher ----------

def apply(client, code):
    return client.post("/api/cart/voucher", json={"code": code})


def test_apply_fixed_voucher_case_insensitive(customer):
    add(customer, 2)  # 400.000
    body = apply(customer, " tanthu ").json()
    assert body["voucher"]["code"] == "TANTHU"
    assert body["discount"] == 50_000 and body["total"] == 350_000


def test_percent_voucher_is_capped(customer):
    add(customer, 2)  # 10% của 400.000 = 40.000, trần 30.000
    assert apply(customer, "GIAM10").json()["discount"] == 30_000


@pytest.mark.parametrize(
    "code,error",
    [
        ("KHONGCO", "VOUCHER_NOT_FOUND"),
        ("TAT", "VOUCHER_NOT_FOUND"),
        ("HETHAN", "VOUCHER_EXPIRED"),
        ("HETLUOT", "VOUCHER_EXHAUSTED"),
    ],
)
def test_invalid_vouchers(customer, code, error):
    add(customer, 2)
    resp = apply(customer, code)
    assert resp.json()["error"]["code"] == error
    assert customer.get("/api/cart").json()["voucher"] is None


def test_min_order_value(customer):
    add(customer, 1)  # 150.000 < 200.000
    resp = apply(customer, "TANTHU")
    assert resp.json()["error"]["code"] == "VOUCHER_MIN_ORDER"
    assert "200.000đ" in resp.json()["error"]["message"]


def test_new_user_only(customer, db):
    db.query(User).update({User.created_at: utcnow() - timedelta(days=31)})
    db.commit()
    add(customer, 2)
    assert apply(customer, "TANTHU").json()["error"]["code"] == "VOUCHER_NEW_USER_ONLY"


def test_cannot_apply_voucher_to_empty_cart(customer):
    assert apply(customer, "GIAM10").json()["error"]["code"] == "CART_EMPTY"


def test_voucher_auto_removed_when_cart_drops_below_minimum(customer):
    add(customer, 2)
    apply(customer, "TANTHU")
    customer.delete("/api/cart/items/2")
    add(customer, 1)  # còn 150.000
    body = customer.get("/api/cart").json()
    assert body["voucher"] is None and body["discount"] == 0
    # thông báo đã được trả về ở lần xem giỏ ngay sau khi giỏ thay đổi
    assert body["notice"] is None or "TANTHU" in body["notice"]


def test_auto_remove_notice(customer):
    add(customer, 1, 2)  # 300.000
    apply(customer, "TANTHU")
    body = customer.patch("/api/cart/items/1", json={"quantity": 1}).json()  # còn 150.000
    assert body["voucher"] is None
    assert "TANTHU" in body["notice"]


def test_remove_voucher(customer):
    add(customer, 2)
    apply(customer, "GIAM10")
    body = customer.delete("/api/cart/voucher").json()
    assert body["voucher"] is None and body["total"] == 400_000
