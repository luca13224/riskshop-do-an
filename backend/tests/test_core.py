"""Test phần lõi: health check và định dạng lỗi thống nhất.

Yêu cầu MariaDB đang chạy (XAMPP). Chạy: python -m pytest -q
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core import errors
from app.core.errors import AppError
from app.main import app

client = TestClient(app)


def test_health_ok_and_has_request_id():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "db": "ok"}
    assert resp.headers["X-Request-ID"]


def test_request_id_is_echoed_back():
    resp = client.get("/api/health", headers={"X-Request-ID": "abc123"})
    assert resp.headers["X-Request-ID"] == "abc123"


def test_unknown_route_uses_error_format():
    resp = client.get("/api/khong-ton-tai")
    assert resp.status_code == 404
    body = resp.json()["error"]
    assert body["code"] == "NOT_FOUND"
    assert body["request_id"] == resp.headers["X-Request-ID"]


# Ứng dụng nhỏ riêng cho test, để thử các loại lỗi mà không đụng vào API thật
_demo = FastAPI()
errors.install(_demo)


class _Item(BaseModel):
    qty: int


@_demo.post("/item")
def _create(item: _Item):
    return item


@_demo.get("/business-error")
def _business_error():
    raise AppError("VOUCHER_EXPIRED", "Mã giảm giá đã hết hạn.", 409)


@_demo.get("/bug")
def _bug():
    raise RuntimeError("chi tiết nội bộ không được lộ ra")


_demo_client = TestClient(_demo, raise_server_exceptions=False)


def test_business_error_format():
    resp = _demo_client.get("/business-error")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "VOUCHER_EXPIRED"


def test_validation_error_lists_fields():
    resp = _demo_client.post("/item", json={"qty": "nhiều"})
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["fields"][0]["field"] == "qty"


def test_unhandled_error_hides_details():
    resp = _demo_client.get("/bug")
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "nội bộ" not in resp.text
