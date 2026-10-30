"""Test luồng case: quyết định -> việc nền -> case -> nhận xử lý -> kết luận (+ duyệt/từ chối đơn)."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core import jobs
from app.core.time import utcnow
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth import service as auth_service
from app.modules.auth.models import ANALYST
from app.modules.cases.models import RiskCase
from app.modules.catalog.models import Product
from app.modules.order.models import COD
from tests.test_risk_scenarios import browse, checkout, customer, shop  # noqa: F401 (fixture shop)
from worker.main import register_handlers

register_handlers()


def staff_client(db, email: str) -> TestClient:
    auth_service.create_user(db, email=email, password="matkhau123", full_name=email.split("@")[0], role=ANALYST)
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"email": email, "password": "matkhau123"}).status_code == 200
    return c


def run_jobs(db) -> int:
    db.rollback()
    return jobs.run_all(db)


def farm_attack(n: int, device: str = "device-farm-case-01") -> None:
    for i in range(1, n + 1):
        c = customer(f"farm{i}.{device}@example.com", device)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        c.post("/api/cart/voucher", json={"code": "TANTHU"})


def review_order(email: str) -> str:
    c = customer(email, f"device-{email}")
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    r = checkout(c, COD)
    assert r.json()["status"] == "PENDING_REVIEW"
    return r.json()["order_code"]


# ---------- Mở case từ quyết định ----------

def test_farm_opens_one_cluster_case_and_attaches_more(shop, db):
    farm_attack(5)  # tài khoản thứ 5: 10 + 50 (thiết bị) + 10 (IP) + 25 (thử mã liên tục) = 95 >= 80
    assert run_jobs(db) == 1
    case = db.scalar(select(RiskCase))
    assert case.policy == "voucher" and case.cluster_key.startswith("device:") and case.status == "OPEN"

    c = customer("farm6.device-farm-case-01@example.com", "device-farm-case-01")
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    c.post("/api/cart/voucher", json={"code": "TANTHU"})
    run_jobs(db)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(RiskCase)) == 1  # gom vào case cũ, không mở case mới

    staff = staff_client(db, "an@riskshop.test")
    detail = staff.get(f"/api/console/cases/{case.case_code}").json()
    assert detail["decision_count"] == 2
    assert len(detail["linked_accounts"]) == 6  # cả cụm tài khoản trên cùng thiết bị
    assert detail["decisions"][0]["hits"]


def test_review_order_opens_cod_case(shop, db):
    code = review_order("moi@example.com")
    run_jobs(db)
    case = db.scalar(select(RiskCase))
    assert case.policy == "cod" and case.order_id is not None
    staff = staff_client(db, "an@riskshop.test")
    detail = staff.get(f"/api/console/cases/{case.case_code}").json()
    assert detail["order"]["order_code"] == code and detail["order"]["status"] == "PENDING_REVIEW"
    assert "12 Láng Hạ" not in str(detail["order"])  # nhân viên chỉ thấy khu vực, không thấy số nhà


# ---------- Xử lý case ----------

def test_claim_then_clear_approves_order(shop, db):
    code = review_order("moi@example.com")
    run_jobs(db)
    case_code = db.scalar(select(RiskCase.case_code))
    staff = staff_client(db, "an@riskshop.test")

    r = staff.post(f"/api/console/cases/{case_code}/resolve", json={"outcome": "CLEARED", "note": "Đã gọi xác nhận"})
    assert r.json()["error"]["code"] == "INVALID_TRANSITION"  # phải nhận xử lý trước

    assert staff.post(f"/api/console/cases/{case_code}/claim").json()["status"] == "IN_REVIEW"
    r = staff.post(f"/api/console/cases/{case_code}/resolve", json={"outcome": "CLEARED", "note": "ngắn"})
    assert r.status_code == 422  # bắt buộc ghi lý do

    r = staff.post(f"/api/console/cases/{case_code}/resolve",
                   json={"outcome": "CLEARED", "note": "Đã gọi điện, khách xác nhận mua thật"})
    body = r.json()
    assert body["status"] == "CLEARED" and body["order"]["status"] == "CONFIRMED"
    assert [a["action"] for a in body["actions"]] == ["open", "claim", "resolve"]

    db.rollback()
    audit = db.scalars(select(AuditLog.action).where(AuditLog.entity_id == case_code)).all()
    assert audit == ["case.claim", "case.resolve"]
    assert code


def test_confirm_abuse_rejects_order_and_restocks(shop, db):
    review_order("moi@example.com")
    run_jobs(db)
    case_code = db.scalar(select(RiskCase.case_code))
    db.rollback()
    stock_before = db.get(Product, 3).stock
    staff = staff_client(db, "an@riskshop.test")
    staff.post(f"/api/console/cases/{case_code}/claim")
    body = staff.post(f"/api/console/cases/{case_code}/resolve",
                      json={"outcome": "CONFIRMED_ABUSE", "note": "Số điện thoại không liên lạc được"}).json()
    assert body["order"]["status"] == "REJECTED"
    db.rollback()
    assert db.get(Product, 3).stock == stock_before + 1


def test_only_assignee_can_resolve(shop, db):
    review_order("moi@example.com")
    run_jobs(db)
    case_code = db.scalar(select(RiskCase.case_code))
    a = staff_client(db, "a@riskshop.test")
    b = staff_client(db, "b@riskshop.test")
    a.post(f"/api/console/cases/{case_code}/claim")
    r = b.post(f"/api/console/cases/{case_code}/resolve", json={"outcome": "CLEARED", "note": "Tôi nghĩ là ổn thôi"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "NOT_ASSIGNEE"


def test_closed_case_frees_cluster_for_new_case(shop, db):
    farm_attack(5)
    run_jobs(db)
    case_code = db.scalar(select(RiskCase.case_code))
    staff = staff_client(db, "an@riskshop.test")
    staff.post(f"/api/console/cases/{case_code}/claim")
    staff.post(f"/api/console/cases/{case_code}/resolve",
               json={"outcome": "CONFIRMED_ABUSE", "note": "Cụm farm voucher rõ ràng"})
    c = customer("farm9.device-farm-case-01@example.com", "device-farm-case-01")  # tái phạm
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    c.post("/api/cart/voucher", json={"code": "TANTHU"})
    run_jobs(db)
    db.rollback()
    assert db.scalar(select(func.count()).select_from(RiskCase)) == 2


def test_customer_cannot_access_cases(shop, db):
    c = customer("khach@example.com", "device-khach-0001")
    assert c.get("/api/console/cases").status_code == 403


def test_case_list_filters(shop, db):
    review_order("moi@example.com")
    run_jobs(db)
    staff = staff_client(db, "an@riskshop.test")
    assert len(staff.get("/api/console/cases").json()) == 1
    assert staff.get("/api/console/cases?status=CLOSED").json() == []


# ---------- Hàng đợi việc nền ----------

def test_job_retries_then_fails(db):
    calls = []

    def flaky(_db, payload):
        calls.append(payload)
        raise RuntimeError("tạm thời lỗi")

    jobs.HANDLERS["flaky"] = flaky
    jobs.enqueue(db, "flaky", {"x": 1})
    db.commit()
    assert jobs.run_once(db) is True
    job = db.scalar(select(jobs.Job))
    assert job.status == jobs.QUEUED and job.attempts == 1 and job.run_after > utcnow()
    assert jobs.run_once(db) is False  # chưa tới giờ thử lại

    job.run_after, job.attempts = utcnow() - timedelta(seconds=1), job.max_attempts - 1
    db.commit()
    jobs.run_once(db)
    db.refresh(job)
    assert job.status == jobs.FAILED and "tạm thời lỗi" in job.last_error
