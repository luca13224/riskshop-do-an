"""Test giới hạn đăng nhập sai và che dữ liệu cá nhân trên Risk Console."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.privacy import mask_email, mask_phone
from app.core.time import utcnow
from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth import service
from app.modules.auth.models import ADMIN, ANALYST, RISK_MANAGER, LoginAttempt

from tests.test_auth import register
from tests.test_risk_scenarios import browse, checkout, customer, shop  # noqa: F401 (fixture shop)


def login(client, email="minh@example.com", password="matkhau123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def staff(db, email: str, role: str) -> TestClient:
    service.create_user(db, email=email, password="matkhau123", full_name=email.split("@")[0], role=role)
    c = TestClient(app)
    assert login(c, email).status_code == 200
    return c


# ---------- Che dữ liệu ----------

def test_mask_helpers():
    assert mask_email("minh.nguyen@gmail.com") == "mi***@gmail.com"
    assert mask_email("ab@x.vn") == "a***@x.vn"
    assert mask_email("khong-co-a-cong") == "***"
    assert mask_phone("0912345678") == "091****678"
    assert mask_phone(None) is None


def test_console_apis_never_return_raw_email(shop, db):
    minh = customer("minh.nguyen@example.com", "device-minh-0001")
    browse(minh)
    minh.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert checkout(minh).status_code == 201
    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)

    orders = manager.get("/api/console/orders").json()["items"]
    assert orders[0]["customer_email"] == "mi***@example.com"
    decisions = manager.get("/api/console/risk/decisions").json()
    assert decisions and decisions[0]["user_email"] == "mi***@example.com" and decisions[0]["user_id"]
    for path in ("/api/console/orders", "/api/console/risk/decisions", "/api/console/cases?status=ALL"):
        assert "minh.nguyen@example.com" not in manager.get(path).text
    # Khách vẫn thấy email đầy đủ của chính mình
    assert minh.get("/api/auth/me").json()["email"] == "minh.nguyen@example.com"


# ---------- Xem liên hệ đầy đủ ----------

def test_manager_reveals_contact_with_reason_and_audit(client, db):
    user_id = register(client, email="minh.nguyen@example.com", phone="0912345678").json()["id"]
    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)

    assert manager.post(f"/api/console/users/{user_id}/reveal-contact", json={"reason": "ngắn"}).status_code == 422
    resp = manager.post(f"/api/console/users/{user_id}/reveal-contact",
                        json={"reason": "Gọi xác minh đơn COD giá trị cao"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "minh.nguyen@example.com" and resp.json()["phone"] == "0912345678"

    db.rollback()
    log = db.scalar(select(AuditLog).where(AuditLog.action == "user.reveal_contact"))
    assert log.entity_id == str(user_id) and "COD" in log.note
    assert "minh.nguyen" not in str(log.after_data) + str(log.before_data)  # không chép PII vào log


def test_analyst_and_customer_cannot_reveal(client, db):
    user_id = register(client).json()["id"]
    analyst = staff(db, "analyst@riskshop.test", ANALYST)
    body = {"reason": "Muốn xem thử thông tin"}
    assert analyst.post(f"/api/console/users/{user_id}/reveal-contact", json=body).status_code == 403
    assert client.post(f"/api/console/users/{user_id}/reveal-contact", json=body).status_code == 403


def test_cannot_reveal_staff_account(db):
    admin = staff(db, "admin@riskshop.test", ADMIN)
    other = service.create_user(db, email="analyst2@riskshop.test", password="x" * 10, full_name="A", role=ANALYST)
    resp = admin.post(f"/api/console/users/{other.id}/reveal-contact", json={"reason": "Kiểm tra quyền hạn"})
    assert resp.status_code == 404


# ---------- Giới hạn đăng nhập sai ----------

def test_account_locked_after_five_failures_even_with_right_password(client):
    register(client)
    for _ in range(5):
        assert login(client, password="sai-mat-khau").status_code == 401
    resp = login(client)
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "LOGIN_RATE_LIMITED"


def test_unknown_email_is_limited_the_same_way(client):
    for _ in range(5):
        assert login(client, email="khongton@example.com", password="x").status_code == 401
    assert login(client, email="khongton@example.com", password="x").status_code == 429


def test_success_resets_account_counter(client):
    register(client)
    for _ in range(4):
        login(client, password="sai")
    assert login(client).status_code == 200
    for _ in range(4):
        assert login(client, password="sai").status_code == 401
    assert login(client).status_code == 200


def test_old_failures_outside_window_do_not_count(client, db):
    register(client)
    for _ in range(5):
        login(client, password="sai")
    db.rollback()
    for a in db.scalars(select(LoginAttempt)):
        a.created_at = utcnow() - timedelta(minutes=16)
    db.commit()
    assert login(client).status_code == 200


def test_ip_limit_across_many_accounts(client):
    # Một IP thử sai trên nhiều email khác nhau (dò mật khẩu hàng loạt)
    for i in range(20):
        assert login(client, email=f"nan{i}@example.com", password="x").status_code == 401
    assert login(client, email="nan99@example.com", password="x").status_code == 429


def test_many_successful_logins_from_one_ip_are_not_limited(client):
    register(client)
    for _ in range(30):
        assert login(client).status_code == 200


def test_attempts_store_hashes_not_email(client, db):
    login(client, email="minh@example.com", password="sai")
    db.rollback()
    a = db.scalar(select(LoginAttempt))
    assert len(a.email_hash) == 64 and "minh" not in a.email_hash
