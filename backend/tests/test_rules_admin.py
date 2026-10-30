"""Test quản lý luật (cảnh 6): phân quyền, phiên bản mới, chỉ sửa con số, luật mới có hiệu lực ngay."""

import copy

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth import service as auth_service
from app.modules.auth.models import ANALYST, RISK_MANAGER
from app.modules.risk.models import Rule, RuleVersion
from tests.test_risk_scenarios import customer, shop  # noqa: F401 (fixture shop)


def login(db, email: str, role: str) -> TestClient:
    auth_service.create_user(db, email=email, password="matkhau123", full_name=email.split("@")[0], role=role)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": email, "password": "matkhau123"})
    return c


def r02(client: TestClient) -> dict:
    return next(r for r in client.get("/api/console/risk/rules").json() if r["code"] == "DEV_MULTI_NEW_ACCOUNTS")


def lowered_threshold(rule: dict) -> dict:
    params = copy.deepcopy(rule["active"]["params"])
    params["tiers"][1]["gte"] = 2  # bậc "≥3 tài khoản mới/thiết bị" hạ xuống "≥2"
    params["tiers"][1]["points"] = 40  # và tăng điểm: 10 (R01) + 40 = 50 -> chạm ngưỡng gỡ voucher
    return params


def test_analyst_can_read_but_not_edit(shop, db):
    analyst = login(db, "an@riskshop.test", ANALYST)
    rule = r02(analyst)
    assert rule["active"]["version"] == 1 and rule["strength"] == "strong"
    r = analyst.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                     json={"params": lowered_threshold(rule), "enabled": True, "change_note": "Thử hạ ngưỡng"})
    assert r.status_code == 403


def test_manager_creates_new_version_old_one_kept(shop, db):
    manager = login(db, "manager@riskshop.test", RISK_MANAGER)
    rule = r02(manager)
    r = manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                     json={"params": lowered_threshold(rule), "enabled": True,
                           "change_note": "Farm mới dùng ít tài khoản hơn, hạ ngưỡng xuống 2"})
    assert r.status_code == 200 and r.json()["active"]["version"] == 2
    versions = manager.get("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions").json()
    assert [v["version"] for v in versions] == [2, 1]
    assert versions[1]["params"]["tiers"][1]["gte"] == 3  # phiên bản cũ giữ nguyên
    assert versions[0]["created_by_name"] == "manager"
    db.rollback()
    log = db.scalar(select(AuditLog).where(AuditLog.action == "rule.new_version"))
    assert log.before_data["version"] == 1 and log.after_data["version"] == 2


def test_new_version_takes_effect_immediately(shop, db):
    manager = login(db, "manager@riskshop.test", RISK_MANAGER)
    manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                 json={"params": lowered_threshold(r02(manager)), "enabled": True,
                       "change_note": "Hạ ngưỡng thiết bị xuống 2 tài khoản"})
    results = []
    for i in range(1, 3):
        c = customer(f"farm{i}@example.com", "device-farm-rule-01")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        results.append(c.post("/api/cart/voucher", json={"code": "TANTHU"}).status_code)
    assert results == [200, 409]  # với luật v1, tài khoản thứ 2 vẫn được dùng (10 điểm)


def test_disable_rule(shop, db):
    manager = login(db, "manager@riskshop.test", RISK_MANAGER)
    rule = r02(manager)
    manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                 json={"params": rule["active"]["params"], "enabled": False, "change_note": "Tạm tắt để kiểm tra"})
    for i in range(1, 4):
        c = customer(f"farm{i}@example.com", "device-farm-rule-02")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        last = c.post("/api/cart/voucher", json={"code": "TANTHU"})
    assert last.status_code == 200  # không còn luật thiết bị: 10 + 10 = 20 điểm


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda p: p.update(feature="product_views_24h"), "không được đổi tên đặc trưng"),
        (lambda p: p["tiers"].append({"gte": 9, "points": 60}), "không được thêm/bớt"),
        (lambda p: p["tiers"][0].update(points=500), "điểm phải trong khoảng"),
        (lambda p: p["tiers"][0].update(gte=-1), "không được âm"),
        (lambda p: p["tiers"][0].update(points="nhiều"), "phải là số"),
    ],
)
def test_only_numbers_can_change(shop, db, mutate, fragment):
    manager = login(db, "manager@riskshop.test", RISK_MANAGER)
    params = copy.deepcopy(r02(manager)["active"]["params"])
    mutate(params)
    r = manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                     json={"params": params, "enabled": True, "change_note": "Thử thay đổi không hợp lệ"})
    assert r.status_code == 422 and fragment in r.json()["error"]["message"]


def test_change_note_required_and_no_op_rejected(shop, db):
    manager = login(db, "manager@riskshop.test", RISK_MANAGER)
    rule = r02(manager)
    r = manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                     json={"params": lowered_threshold(rule), "enabled": True, "change_note": "ngắn"})
    assert r.status_code == 422
    r = manager.post("/api/console/risk/rules/DEV_MULTI_NEW_ACCOUNTS/versions",
                     json={"params": rule["active"]["params"], "enabled": True, "change_note": "Không đổi gì cả nhé"})
    assert r.json()["error"]["code"] == "NO_CHANGE"
    db.rollback()
    rule_row = db.scalar(select(Rule).where(Rule.code == "DEV_MULTI_NEW_ACCOUNTS"))
    assert db.get(RuleVersion, rule_row.active_version_id).version == 1


def test_hit_counts(shop, db):
    c = customer("minh@example.com", "device-minh-rule")
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    c.post("/api/cart/voucher", json={"code": "TANTHU"})
    analyst = login(db, "an@riskshop.test", ANALYST)
    rules = {r["code"]: r["hit_count_7d"] for r in analyst.get("/api/console/risk/rules").json()}
    assert rules["VCH_NEW_ACCOUNT"] == 1 and rules["DEV_MULTI_NEW_ACCOUNTS"] == 0
