"""Kiểm tra Risk API giả: mỗi mã kích hoạt phải cho đúng quyết định và hành động.

Chạy: python -m pytest -q
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def evaluate(**body):
    resp = client.post("/v1/evaluate", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_allow_by_default():
    r = evaluate(event="checkout", customer_email="an@example.com",
                 coupon_codes=["TANTHU"], payment_method="cod", order_total=250000)
    assert r["decision"] == "ALLOW"
    assert r["actions"] == {"remove_coupons": [], "disable_cod": False,
                            "hold_order": False, "block": False}


def test_remove_only_farm_coupon():
    r = evaluate(event="cart_update", customer_email="an@example.com",
                 coupon_codes=["FARM50", "TANTHU"])
    assert r["decision"] == "ALLOW_WITH_RESTRICTION"
    assert r["actions"]["remove_coupons"] == ["FARM50"]


def test_disable_cod():
    r = evaluate(event="payment_methods", customer_email="an+nocod@example.com")
    assert r["actions"]["disable_cod"] is True


def test_review_only_at_checkout():
    assert evaluate(event="cart_update", customer_email="an+review@example.com")["decision"] == "ALLOW"
    r = evaluate(event="checkout", customer_email="an+review@example.com")
    assert r["decision"] == "REVIEW"
    assert r["actions"]["hold_order"] is True


def test_block_has_generic_message():
    r = evaluate(event="checkout", customer_email="an+block@example.com")
    assert r["decision"] == "BLOCK"
    assert r["actions"]["block"] is True
    assert "luật" not in r["customer_message"].lower()


def test_unknown_event_is_rejected():
    resp = client.post("/v1/evaluate", json={"event": "hack"})
    assert resp.status_code == 422
