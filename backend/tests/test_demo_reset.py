"""Test demo reset: sau khi reset, các nhân vật cho đúng kết quả của kịch bản demo."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import app
from app.modules.auth.models import User
from app.modules.catalog.models import Product
from app.modules.catalog.seed import PRODUCTS
from app.modules.lab.reset import reset
from app.modules.order.models import Order
from app.modules.risk.models import Rule

ADDRESS = {"recipient_name": "Khách", "phone": "0901234567", "line": "12 Láng Hạ",
           "ward": "Thành Công", "district": "Ba Đình", "province": "Hà Nội"}


def login(email: str, password: str, device: str) -> TestClient:
    c = TestClient(app, client=("203.0.113.50", 50000))
    c.headers["X-Device-Id"] = device
    assert c.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200
    return c


def product_id(db, sku: str) -> int:
    return db.scalar(select(Product.id).where(Product.sku == sku))


def test_reset_creates_baseline(db):
    creds = reset(db)
    assert set(creds) >= {"minh@shop.test", "khang@shop.test", "lan@shop.test", "admin@riskshop.test"}
    assert db.scalar(select(func.count()).select_from(Product)) == len(PRODUCTS)
    assert db.scalar(select(func.count()).select_from(Rule)) == 10
    lan_id = db.scalar(select(User.id).where(User.email == "lan@shop.test"))
    assert db.scalar(select(func.count()).select_from(Order).where(Order.user_id == lan_id)) == 30

    # Chạy lại lần 2: vẫn đúng trạng thái chuẩn (không cộng dồn dữ liệu)
    reset(db)
    assert db.scalar(select(func.count()).select_from(User)) == 6


def test_personas_behave_as_in_demo_script(db):
    assert_demo_personas(db, reset(db))


def assert_demo_personas(db, creds: dict[str, str]) -> None:
    """Ba nhân vật của kịch bản demo cho ra đúng kết quả (dùng lại sau khi sinh lịch sử mô phỏng)."""
    aria, viewpro = product_id(db, "AU-001"), product_id(db, "CP-003")

    # Cảnh 1: Minh (khách mới hợp lệ) dùng TANTHU được
    minh = login("minh@shop.test", creds["minh@shop.test"], "device-minh-demo")
    minh.post("/api/cart/items", json={"product_id": aria, "quantity": 1})
    assert minh.post("/api/cart/voucher", json={"code": "TANTHU"}).status_code == 200

    # Cảnh 5a: Khang (4/5 đơn COD thất bại) không được COD
    khang = login("khang@shop.test", creds["khang@shop.test"], "device-khang-demo")
    khang.post("/api/cart/items", json={"product_id": aria, "quantity": 1})
    assert khang.get("/api/orders/payment-options").json()["cod_allowed"] is False

    # Cảnh 5c: Lan (30 đơn giao thành công) đặt COD 5,49 triệu vẫn được xác nhận ngay
    lan = login("lan@shop.test", creds["lan@shop.test"], "device-lan-demo")
    lan.post("/api/cart/items", json={"product_id": viewpro, "quantity": 1})
    r = lan.post("/api/orders/checkout", json={"address": ADDRESS, "payment_method": "COD"},
                 headers={"Idempotency-Key": str(uuid.uuid4())})
    assert r.status_code == 201 and r.json()["status"] == "CONFIRMED"
