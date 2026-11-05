"""Test chạy thử luật trên quyết định cũ (backtest): chỉ đọc, đo đúng hướng thay đổi, phân quyền."""

import copy

from sqlalchemy import func, select

from app.modules.auth.models import ANALYST
from app.modules.risk.models import RuleVersion
from tests.test_risk_scenarios import add_history, browse, customer, shop  # noqa: F401 (fixture shop)
from tests.test_rules_admin import login

URL = "/api/console/risk/rules/COD_FAIL_RATE/backtest"


def r07_params(client) -> dict:
    rule = next(r for r in client.get("/api/console/risk/rules").json() if r["code"] == "COD_FAIL_RATE")
    return copy.deepcopy(rule["active"]["params"])


def bomber_sees_payment_options(db, email="bom@example.com", delivered=1, failed=2):
    c = customer(email, f"device-{email}")
    add_history(db, email, cod_delivered=delivered, cod_failed=failed)
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert c.get("/api/orders/payment-options").json()["cod_allowed"] is (failed == 0)


def test_same_params_change_nothing_and_replay_matches_reality(shop, db):
    bomber_sees_payment_options(db)
    analyst = login(db, "an@riskshop.test", ANALYST)
    r = analyst.post(URL, json={"params": r07_params(analyst), "days": 7})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["decisions_scanned"] >= 1 and body["replay_agreement"] == 1.0
    assert body["hits_old"] == body["hits_new"] == 1
    assert body["stricter"]["decisions"] == body["looser"]["decisions"] == 0


def test_lower_points_shows_looser_decision_without_saving(shop, db):
    bomber_sees_payment_options(db)  # làm mượt 3/13 = 0,23: bậc 0,20 (+40) đang ẩn COD
    analyst = login(db, "an@riskshop.test", ANALYST)
    params = r07_params(analyst)
    params["tiers"][1]["points"] = 25  # quay về trước ADR-014
    versions = db.scalar(select(func.count()).select_from(RuleVersion))
    body = analyst.post(URL, json={"params": params, "days": 7}).json()
    looser = body["looser"]
    assert looser["decisions"] == 1 and looser["accounts"] == 1
    sample = looser["samples"][0]
    assert sample["before"] == "ALLOW_WITH_RESTRICTION" and sample["after"] == "ALLOW"
    assert "***@" in sample["user_email"]  # email bị che như mọi chỗ khác trên Console
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(RuleVersion)) == versions  # chỉ đọc, không tạo phiên bản


def test_disabling_rule_and_rejecting_shape_changes(shop, db):
    bomber_sees_payment_options(db)
    analyst = login(db, "an@riskshop.test", ANALYST)
    params = r07_params(analyst)
    body = analyst.post(URL, json={"params": params, "enabled": False, "days": 7}).json()
    assert body["hits_new"] == 0 and body["looser"]["decisions"] == 1
    params["tiers"].pop()  # bỏ một bậc: đổi cấu trúc, không cho
    assert analyst.post(URL, json={"params": params}).status_code == 422


def test_customer_cannot_backtest(shop, db):
    c = customer("khach@example.com", "device-khach-0001")
    assert c.post(URL, json={"params": {}}).status_code == 403
