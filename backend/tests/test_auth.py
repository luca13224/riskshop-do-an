"""Test module auth: đăng ký, đăng nhập, phiên, phân quyền, ghi nhận thiết bị và IP."""

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core import errors
from app.core.config import get_settings
from app.core.db import get_db
from app.modules.auth import security, service
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, ANALYST, AuthSession, User, UserDevice, UserIp

from tests.conftest import _get_test_db

COOKIE = get_settings().session_cookie_name
DEVICE = {"X-Device-Id": "device-test-0001"}


def register(client, email="minh@example.com", password="matkhau123", **extra):
    body = {"email": email, "password": password, "full_name": "Nguyễn Minh", **extra}
    return client.post("/api/auth/register", json=body, headers=DEVICE)


# ---------- Đăng ký ----------

def test_register_creates_customer_and_logs_in(client):
    resp = register(client, email="  Minh@Example.COM ")
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "minh@example.com"  # đã chuẩn hóa
    assert body["role"] == "customer"
    assert "password" not in resp.text and "password_hash" not in resp.text
    assert COOKIE in resp.cookies
    assert client.get("/api/auth/me").json()["email"] == "minh@example.com"


def test_register_cannot_choose_role(client):
    resp = register(client, role="admin")
    assert resp.status_code == 201
    assert resp.json()["role"] == "customer"


def test_register_duplicate_email(client):
    register(client)
    resp = register(client, email="MINH@example.com")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_TAKEN"


def test_register_duplicate_phone(client):
    register(client, phone="0901234567")
    resp = register(client, email="khac@example.com", phone="0901234567")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "PHONE_TAKEN"


def test_register_validation(client):
    resp = register(client, email="khong-phai-email", password="ngan")
    assert resp.status_code == 422
    fields = {f["field"] for f in resp.json()["error"]["fields"]}
    assert {"email", "password"} <= fields


def test_password_is_hashed_with_argon2(client, db):
    register(client)
    user = db.scalar(select(User))
    assert user.password_hash.startswith("$argon2")
    assert "matkhau123" not in user.password_hash


# ---------- Đăng nhập, đăng xuất ----------

def test_login_wrong_password_and_unknown_email_look_the_same(client):
    register(client)
    client.cookies.clear()
    wrong_pw = client.post("/api/auth/login", json={"email": "minh@example.com", "password": "sai-mat-khau"})
    unknown = client.post("/api/auth/login", json={"email": "ai@example.com", "password": "sai-mat-khau"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json()["error"]["message"] == unknown.json()["error"]["message"]


def test_login_then_me(client):
    register(client)
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401
    resp = client.post("/api/auth/login", json={"email": "MINH@example.com", "password": "matkhau123"})
    assert resp.status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_session_cookie_is_httponly(client):
    resp = register(client)
    set_cookie = resp.headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_logout_revokes_session_on_server(client, db):
    register(client)
    token = client.cookies.get(COOKIE)
    assert client.post("/api/auth/logout").status_code == 204
    # Kể cả ai đó còn giữ token cũ, server vẫn từ chối
    client.cookies.set(COOKIE, token)
    assert client.get("/api/auth/me").status_code == 401
    assert db.scalar(select(AuthSession.revoked_at)) is not None


def test_locked_account_cannot_login_and_loses_session(client, db):
    register(client)
    db.query(User).update({User.status: "locked"})
    db.commit()
    assert client.get("/api/auth/me").status_code == 401
    resp = client.post("/api/auth/login", json={"email": "minh@example.com", "password": "matkhau123"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_session_token_stored_only_as_hash(client, db):
    register(client)
    token = client.cookies.get(COOKIE)
    stored = db.scalar(select(AuthSession.token_hash))
    assert stored != token
    assert stored == security.hash_token(token)


# ---------- Ghi nhận thiết bị và IP (nguyên liệu cho luật rủi ro) ----------

def test_device_and_ip_recorded_once_per_user(client, db):
    register(client)
    client.post("/api/auth/login", json={"email": "minh@example.com", "password": "matkhau123"}, headers=DEVICE)
    assert db.scalar(select(func.count()).select_from(UserDevice)) == 1
    ip_row = db.scalar(select(UserIp))
    assert ip_row is not None
    assert len(ip_row.ip_hash) == 64


def test_two_accounts_same_device_share_device_row(client, db):
    register(client, email="a@example.com")
    client.cookies.clear()
    register(client, email="b@example.com")
    rows = db.execute(select(UserDevice.device_id)).scalars().all()
    assert len(rows) == 2 and rows[0] == rows[1]


def test_invalid_device_header_is_ignored(client, db):
    client.post(
        "/api/auth/register",
        json={"email": "x@example.com", "password": "matkhau123", "full_name": "X"},
        headers={"X-Device-Id": "<script>"},
    )
    assert db.scalar(select(func.count()).select_from(UserDevice)) == 0


def test_mask_ip():
    assert security.mask_ip("113.161.45.10") == "113.161.x.x"
    assert security.mask_ip("2001:db8:1:2::5") == "2001:0db8:x:x::"
    assert security.mask_ip("khong-phai-ip") == "unknown"


# ---------- Phân quyền ----------

_guarded = FastAPI()
errors.install(_guarded)
_guarded.dependency_overrides[get_db] = _get_test_db


@_guarded.get("/console-only")
def _console_only(user=Depends(require_roles(ANALYST, ADMIN))):
    return {"role": user.role}


def test_require_roles(db):
    service.create_user(db, email="analyst@riskshop.test", password="matkhau123", full_name="A", role=ANALYST)
    ctx = service.ClientContext(device_uid=None, ip=None)
    _, staff_token = service.login(db, "analyst@riskshop.test", "matkhau123", ctx)

    service.create_user(db, email="khach@example.com", password="matkhau123", full_name="K", role="customer")
    _, customer_token = service.login(db, "khach@example.com", "matkhau123", ctx)

    c = TestClient(_guarded)
    assert c.get("/console-only").status_code == 401
    c.cookies.set(COOKIE, customer_token)
    resp = c.get("/console-only")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
    c.cookies.set(COOKIE, staff_token)
    assert c.get("/console-only").json() == {"role": "analyst"}
