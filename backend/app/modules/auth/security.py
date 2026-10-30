"""Các hàm bảo mật thuần (không đụng CSDL), dễ test riêng."""

import hashlib
import hmac
import ipaddress
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()  # Argon2id với tham số mặc định của thư viện
# Băm sẵn một mật khẩu giả: khi email không tồn tại vẫn chạy verify,
# để thời gian phản hồi không tiết lộ email nào đã đăng ký.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_ip(ip: str, secret: str) -> str:
    return hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()


def mask_ip(ip: str) -> str:
    """113.161.45.10 -> 113.161.x.x ; 2001:db8:1:2::5 -> 2001:db8:x:x::"""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    if addr.version == 4:
        a, b, *_ = ip.split(".")
        return f"{a}.{b}.x.x"
    groups = addr.exploded.split(":")
    return f"{groups[0]}:{groups[1]}:x:x::"
