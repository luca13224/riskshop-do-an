"""Logic nghiệp vụ của module auth.

Các module khác chỉ được gọi các hàm công khai ở đây (không tự truy vấn bảng của auth).
"""

import re
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.auth import security
from app.modules.auth.models import CUSTOMER, AuthSession, Device, User, UserDevice, UserIp
from app.modules.auth.schemas import RegisterIn

_DEVICE_UID_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


@dataclass(frozen=True)
class ClientContext:
    """Thông tin về nơi gửi request: thiết bị và IP. Là nguyên liệu cho luật rủi ro."""

    device_uid: str | None
    ip: str | None


def normalize_device_uid(raw: str | None) -> str | None:
    # Giá trị do trình duyệt gửi lên nên không tin: sai định dạng thì coi như không có
    return raw if raw and _DEVICE_UID_RE.match(raw) else None


def register_customer(db: Session, data: RegisterIn, ctx: ClientContext) -> tuple[User, str]:
    """Tạo tài khoản khách hàng rồi đăng nhập luôn. Trả về (user, token phiên)."""
    user = User(
        email=data.email,
        phone=data.phone,
        full_name=data.full_name,
        password_hash=security.hash_password(data.password),
        role=CUSTOMER,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # Ràng buộc UNIQUE ở CSDL là hàng rào cuối, kể cả khi hai request đăng ký cùng lúc
        if "phone" in str(exc.orig):
            raise AppError("PHONE_TAKEN", "Số điện thoại này đã được dùng.", 409) from exc
        raise AppError("EMAIL_TAKEN", "Email này đã được đăng ký.", 409) from exc
    token = _start_session(db, user, ctx)
    db.commit()
    return user, token


def create_user(db: Session, *, email: str, password: str, full_name: str, role: str) -> User:
    """Tạo tài khoản với vai trò bất kỳ. Chỉ dùng từ CLI/seed, không mở qua API."""
    user = User(email=email, full_name=full_name, role=role, password_hash=security.hash_password(password))
    db.add(user)
    db.commit()
    return user


def login(db: Session, email: str, password: str, ctx: ClientContext) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == email))
    password_ok = security.verify_password(user.password_hash if user else None, password)
    if user is None or not password_ok:
        # Cùng một thông điệp cho "sai email" và "sai mật khẩu", để không lộ email nào tồn tại
        raise AppError("INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng.", 401)
    if user.status != "active":
        raise AppError("ACCOUNT_LOCKED", "Tài khoản đang bị khóa. Vui lòng liên hệ hỗ trợ.", 403)
    token = _start_session(db, user, ctx)
    db.commit()
    return user, token


def logout(db: Session, token: str) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == security.hash_token(token)))
    if session and session.revoked_at is None:
        session.revoked_at = utcnow()
        db.commit()


def get_user_by_token(db: Session, token: str) -> User | None:
    now = utcnow()
    row = db.execute(
        select(User)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == security.hash_token(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
            User.status == "active",
        )
    ).scalar_one_or_none()
    return row


def _start_session(db: Session, user: User, ctx: ClientContext) -> str:
    device_id = _record_client(db, user, ctx)
    token = security.new_session_token()
    db.add(
        AuthSession(
            token_hash=security.hash_token(token),
            user_id=user.id,
            device_id=device_id,
            expires_at=utcnow() + timedelta(hours=get_settings().session_ttl_hours),
        )
    )
    return token


def _record_client(db: Session, user: User, ctx: ClientContext) -> int | None:
    """Ghi nhận thiết bị và IP mà tài khoản vừa dùng (nguyên liệu cho luật R02, R04).

    Dùng INSERT ... ON DUPLICATE KEY UPDATE để an toàn khi nhiều request đến cùng lúc.
    """
    now = utcnow()
    device_id = None
    if ctx.device_uid:
        db.execute(
            mysql_insert(Device)
            .values(device_uid=ctx.device_uid, first_seen_at=now)
            .on_duplicate_key_update(device_uid=ctx.device_uid)
        )
        device_id = db.scalar(select(Device.id).where(Device.device_uid == ctx.device_uid))
        db.execute(
            mysql_insert(UserDevice)
            .values(user_id=user.id, device_id=device_id, first_seen_at=now, last_seen_at=now)
            .on_duplicate_key_update(last_seen_at=now)
        )
    if ctx.ip:
        db.execute(
            mysql_insert(UserIp)
            .values(
                user_id=user.id,
                ip_hash=security.hash_ip(ctx.ip, get_settings().ip_hash_secret),
                ip_masked=security.mask_ip(ctx.ip),
                first_seen_at=now,
                last_seen_at=now,
            )
            .on_duplicate_key_update(last_seen_at=now)
        )
    return device_id
