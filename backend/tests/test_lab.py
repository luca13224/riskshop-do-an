"""Test Attack Lab: chạy trọn 4 kịch bản demo qua API thật, mọi bước phải khớp kỳ vọng."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core import jobs
from app.core.config import get_settings
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import ADMIN, ANALYST
from app.modules.cases.models import RiskCase
from app.modules.catalog.models import Product
from app.modules.lab import service as lab
from app.modules.lab.models import LabRun
from app.modules.promotion.models import FIXED, Voucher
from app.modules.risk.seed import seed_rules
from worker.main import register_handlers

register_handlers()


def _client_factory(headers: dict) -> TestClient:
    return TestClient(app, base_url="http://testserver/api", headers=headers)


@pytest.fixture
def lab_shop(db):
    seed_rules(db)
    db.add_all([
        Product(sku="AU-001", slug="tai-nghe-aria", name="Tai nghe không dây Aria", category="audio",
                price=590_000, stock=500),
        Product(sku="CP-003", slug="man-hinh-viewpro", name="Màn hình 27 inch ViewPro", category="computer",
                price=5_490_000, stock=50),
        Product(sku="HM-001", slug="binh-giu-nhiet", name="Bình giữ nhiệt Lumi 500ml", category="home",
                price=249_000, stock=500),
        Voucher(code="TANTHU", discount_type=FIXED, amount=50_000, min_order_value=200_000,
                new_user_only=True, risk_checked=True),
    ])
    db.commit()


@pytest.fixture
def admin(db) -> TestClient:
    auth_service.create_user(db, email="admin@riskshop.test", password="matkhau123", full_name="Admin", role=ADMIN)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "admin@riskshop.test", "password": "matkhau123"})
    return c


def run_scenario(db, admin: TestClient, scenario: str) -> LabRun:
    r = admin.post("/api/console/lab/runs", json={"scenario": scenario})
    assert r.status_code == 202, r.text
    db.rollback()
    lab.execute(db, {"run_id": r.json()["id"]}, client_factory=_client_factory, pause=0)
    db.rollback()
    return db.get(LabRun, r.json()["id"])


@pytest.mark.parametrize("scenario", ["farm_voucher", "family_wifi", "cod_high_value", "cod_bad_history"])
def test_scenario_matches_expectations(lab_shop, admin, db, scenario):
    run = run_scenario(db, admin, scenario)
    failed = [s for s in run.steps if s["ok"] is False]
    assert run.status == "done" and run.passed, (run.summary, failed)


def test_farm_scenario_opens_cluster_case(lab_shop, admin, db):
    run_scenario(db, admin, "farm_voucher")
    jobs.run_all(db)
    db.rollback()
    cases = db.scalars(select(RiskCase)).all()
    assert any(c.policy == "voucher" and c.cluster_key.startswith("device:") for c in cases)


def test_lab_is_admin_only(lab_shop, db):
    auth_service.create_user(db, email="an@riskshop.test", password="matkhau123", full_name="An", role=ANALYST)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": "an@riskshop.test", "password": "matkhau123"})
    assert c.post("/api/console/lab/runs", json={"scenario": "farm_voucher"}).status_code == 403


def test_lab_hidden_when_demo_mode_off(lab_shop, admin, monkeypatch):
    monkeypatch.setattr(get_settings(), "demo_mode", False)
    assert admin.post("/api/console/lab/runs", json={"scenario": "farm_voucher"}).status_code == 404
    assert admin.get("/api/console/lab/scenarios").status_code == 404


def test_unknown_scenario(lab_shop, admin):
    assert admin.post("/api/console/lab/runs", json={"scenario": "xoa_database"}).status_code == 404
