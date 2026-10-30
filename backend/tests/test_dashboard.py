"""Test API dashboard tổng quan: số liệu shop, chuỗi theo ngày, việc cần xử lý, che email, phân quyền."""

from datetime import timedelta

from app.core.time import utcnow
from app.modules.auth.models import ANALYST
from app.modules.order.models import Order
from tests.test_privacy import staff
from tests.test_risk_scenarios import browse, checkout, customer, shop  # noqa: F401 (fixture shop)


def test_dashboard_counts_orders_and_fills_every_day(shop, db):
    for i in range(2):
        c = customer(f"khach{i}@example.com", f"device-khach-{i:04d}")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        assert checkout(c).status_code == 201
    analyst = staff(db, "an@riskshop.test", ANALYST)

    body = analyst.get("/api/console/dashboard", params={"days": 7}).json()
    assert body["current"]["orders"] == 2
    assert body["current"]["gmv"] == 2 * 300_000
    assert body["current"]["cod_orders"] == 2
    assert body["current"]["new_customers"] == 2
    assert body["previous"]["orders"] == 0
    assert len(body["series"]) == 7  # đủ 7 ngày, kể cả ngày không có đơn
    assert sum(d["orders"] for d in body["series"]) == 2
    assert body["current"]["decisions"] == sum(
        d["ALLOW"] + d["ALLOW_WITH_RESTRICTION"] + d["REVIEW"] + d["BLOCK"] for d in body["series"]
    )


def test_old_orders_fall_into_previous_period(shop, db):
    c = customer("cu@example.com", "device-cu-0001")
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert checkout(c).status_code == 201
    db.rollback()
    order = db.query(Order).one()
    order.created_at = utcnow() - timedelta(days=10)
    db.commit()
    body = staff(db, "an@riskshop.test", ANALYST).get("/api/console/dashboard").json()
    assert body["current"]["orders"] == 0 and body["previous"]["orders"] == 1


def test_attention_and_recent_interventions_are_masked(shop, db):
    # Màn hình 5,49 triệu, tài khoản mới, COD -> giữ chờ duyệt (cảnh 5b)
    c = customer("minh.nguyen@example.com", "device-minh-0001")
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    assert checkout(c).status_code == 201
    analyst = staff(db, "an@riskshop.test", ANALYST)
    body = analyst.get("/api/console/dashboard").json()
    assert body["attention"]["pending_orders"] == 1
    recent = body["recent_interventions"]
    assert recent and recent[0]["decision"] == "REVIEW"
    assert recent[0]["user_email"] == "mi***@example.com"
    assert "minh.nguyen@example.com" not in str(body)


def test_dashboard_permissions_and_validation(shop, db, client):
    assert client.get("/api/console/dashboard").status_code == 401
    analyst = staff(db, "an@riskshop.test", ANALYST)
    assert analyst.get("/api/console/dashboard", params={"days": 91}).status_code == 422
    r = analyst.get("/api/console/dashboard", params={"days": 30})
    assert r.status_code == 200, r.text
    assert r.json()["days"] == 30
