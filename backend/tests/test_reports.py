"""Test báo cáo KPI và audit log, dựa trên dữ liệu do Attack Lab tạo ra."""

from fastapi.testclient import TestClient

from app.core import jobs
from app.main import app
from app.modules.auth import service as auth_service
from app.modules.auth.models import ANALYST, RISK_MANAGER
from tests.test_lab import admin, lab_shop, run_scenario  # noqa: F401 (fixtures)


def login(db, email, role) -> TestClient:
    auth_service.create_user(db, email=email, password="matkhau123", full_name=email.split("@")[0], role=role)
    c = TestClient(app)
    c.post("/api/auth/login", json={"email": email, "password": "matkhau123"})
    return c


def test_kpi_after_lab_runs(lab_shop, admin, db):
    run_scenario(db, admin, "farm_voucher")
    run_scenario(db, admin, "cod_high_value")
    jobs.run_all(db)
    db.rollback()
    k = admin.get("/api/console/reports/kpi?days=7").json()
    assert k["decisions"]["total"] > 0 and k["decisions"]["by_decision"]["REVIEW"] == 1
    assert k["latency_ms"]["p50"] is not None and k["latency_ms"]["p50"] <= k["latency_ms"]["p95"] <= k["latency_ms"]["p99"]
    # 4 tài khoản farm bị gỡ NGUOIMOI (50.000đ mỗi tài khoản)
    assert k["impact"]["voucher_blocked_accounts"] == 4 and k["impact"]["voucher_saved_vnd"] == 200_000
    assert k["impact"]["orders_held"] == 1
    assert k["cases"]["by_status"]["OPEN"] == 2
    codes = {r["code"] for r in k["rules"]}
    assert {"DEV_MULTI_NEW_ACCOUNTS", "COD_HIGH_VALUE_LOW_HISTORY"} <= codes
    assert k["assumptions"]


def test_rule_precision_from_case_outcomes(lab_shop, admin, db):
    run_scenario(db, admin, "cod_high_value")
    jobs.run_all(db)
    db.rollback()
    case = admin.get("/api/console/cases").json()[0]["case_code"]
    admin.post(f"/api/console/cases/{case}/claim")
    admin.post(f"/api/console/cases/{case}/resolve", json={"outcome": "CLEARED", "note": "Khách xác nhận mua thật"})
    k = admin.get("/api/console/reports/kpi").json()
    r08 = next(r for r in k["rules"] if r["code"] == "COD_HIGH_VALUE_LOW_HISTORY")
    assert r08["cases_cleared"] == 1 and r08["precision"] == 0.0
    assert k["impact"]["legit_customers_held_by_mistake"] == 1


def test_audit_log_visibility(lab_shop, admin, db):
    run_scenario(db, admin, "family_wifi")
    logs = admin.get("/api/console/audit").json()
    assert logs[0]["action"] == "lab.start" and logs[0]["actor_role"] == "admin"
    assert admin.get("/api/console/audit?entity_type=rule").json() == []
    manager = login(db, "m@riskshop.test", RISK_MANAGER)
    assert manager.get("/api/console/audit").status_code == 200
    analyst = login(db, "a@riskshop.test", ANALYST)
    assert analyst.get("/api/console/audit").status_code == 403  # người bị giám sát không xem/sửa nhật ký
    assert analyst.get("/api/console/reports/kpi").status_code == 200
