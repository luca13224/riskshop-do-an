"""Logic nghiệp vụ của module auth.

Các module khác chỉ được gọi các hàm công khai ở đây (không tự truy vấn bảng của auth).
"""

import re
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.auth import security
from app.modules.auth.models import CUSTOMER, AuthSession, Device, LoginAttempt, User, UserDevice, UserIp
from app.modules.audit import service as audit
from app.modules.auth.schemas import ContactOut, RegisterIn
from app.modules.events import models as event_types
from app.modules.events import service as events

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
    events.record(db, event_types.SIGNUP, user_id=user.id, device_uid=ctx.device_uid, ip=ctx.ip)
    db.commit()
    return user, token


def create_user(db: Session, *, email: str, password: str, full_name: str, role: str) -> User:
    """Tạo tài khoản với vai trò bất kỳ. Chỉ dùng từ CLI/seed, không mở qua API."""
    user = User(email=email, full_name=full_name, role=role, password_hash=security.hash_password(password))
    db.add(user)
    db.commit()
    return user


def _login_failures(db: Session, email_hash: str, ip_hash: str | None) -> tuple[int, int]:
    """Đếm số lần đăng nhập SAI gần đây: (theo tài khoản, theo IP).

    Theo tài khoản: chỉ đếm từ lần đăng nhập đúng gần nhất, để chủ tài khoản gõ nhầm vài lần
    rồi đăng nhập được thì bộ đếm về 0.
    Chỉ đếm lần sai, nên một IP đăng nhập đúng nhiều lần (văn phòng, Attack Lab) không bị chặn.
    """
    since = utcnow() - timedelta(minutes=get_settings().login_window_minutes)
    last_ok = db.scalar(select(func.max(LoginAttempt.created_at))
                        .where(LoginAttempt.email_hash == email_hash, LoginAttempt.success.is_(True)))
    account_since = max(since, last_ok) if last_ok else since
    by_account = db.scalar(select(func.count()).where(
        LoginAttempt.email_hash == email_hash, LoginAttempt.success.is_(False),
        LoginAttempt.created_at > account_since))
    by_ip = db.scalar(select(func.count()).where(
        LoginAttempt.ip_hash == ip_hash, LoginAttempt.success.is_(False),
        LoginAttempt.created_at > since)) if ip_hash else 0
    return by_account, by_ip


def login(db: Session, email: str, password: str, ctx: ClientContext) -> tuple[User, str]:
    settings = get_settings()
    email_hash = security.hash_ip(email.strip().lower(), settings.ip_hash_secret)  # cùng hàm HMAC, khác dữ liệu
    ip_hash = security.hash_ip(ctx.ip, settings.ip_hash_secret) if ctx.ip else None
    by_account, by_ip = _login_failures(db, email_hash, ip_hash)
    # Kiểm tra TRƯỚC khi so mật khẩu: đã quá giới hạn thì mật khẩu đúng cũng không được thử tiếp.
    # Áp dụng cả với email không tồn tại, nên kẻ tấn công không dùng chỗ này để dò email.
    if by_account >= settings.login_max_failures_per_account or by_ip >= settings.login_max_failures_per_ip:
        raise AppError("LOGIN_RATE_LIMITED", f"Bạn đã nhập sai quá nhiều lần. Vui lòng thử lại sau "
                       f"{settings.login_window_minutes} phút.", 429)

    user = db.scalar(select(User).where(User.email == email))
    password_ok = security.verify_password(user.password_hash if user else None, password)
    db.add(LoginAttempt(email_hash=email_hash, ip_hash=ip_hash, success=bool(user and password_ok)))
    if user is None or not password_ok:
        db.commit()  # lưu lần thử sai trước khi báo lỗi
        # Cùng một thông điệp cho "sai email" và "sai mật khẩu", để không lộ email nào tồn tại
        raise AppError("INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng.", 401)
    if user.status != "active":
        raise AppError("ACCOUNT_LOCKED", "Tài khoản đang bị khóa. Vui lòng liên hệ hỗ trợ.", 403)
    token = _start_session(db, user, ctx)
    events.record(db, event_types.LOGIN, user_id=user.id, device_uid=ctx.device_uid, ip=ctx.ip)
    db.commit()
    return user, token


def accounts_on_device(db: Session, device_id: int) -> list[dict]:
    """Hàm công khai cho module cases: các tài khoản từng dùng một thiết bị (bằng chứng liên kết)."""
    rows = db.execute(
        select(User.id, User.email, User.full_name, User.created_at, UserDevice.last_seen_at)
        .join(UserDevice, UserDevice.user_id == User.id)
        .where(UserDevice.device_id == device_id)
        .order_by(User.created_at)
    ).all()
    return [
        {"user_id": r.id, "email": r.email, "full_name": r.full_name, "created_at": r.created_at,
         "last_seen_at": r.last_seen_at}
        for r in rows
    ]


def reveal_contact(db: Session, actor: User, user_id: int, reason: str) -> ContactOut:
    """Xem email/SĐT đầy đủ của một khách hàng. Console mặc định chỉ thấy bản đã che.

    Mỗi lần xem ghi một dòng audit kèm lý do: ai xem, xem của ai, lúc nào, vì sao.
    Audit chỉ ghi user_id, không chép lại email/SĐT vào log.
    """
    user = db.get(User, user_id)
    if user is None or user.role != CUSTOMER:
        raise AppError("USER_NOT_FOUND", "Không tìm thấy khách hàng.", 404)
    audit.record(db, actor_id=actor.id, action="user.reveal_contact", entity_type="user", entity_id=str(user.id), note=reason)
    db.commit()
    return ContactOut(user_id=user.id, full_name=user.full_name, email=user.email, phone=user.phone)


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
    device_id = record_client(db, user, ctx)
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


def record_client(db: Session, user: User, ctx: ClientContext) -> int | None:
    """Ghi nhận thiết bị và IP mà tài khoản vừa dùng (nguyên liệu cho luật R02, R04).

    Hàm công khai: module risk gọi trước mỗi lần chấm điểm để số liệu luôn mới.

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
