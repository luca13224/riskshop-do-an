"""Bảng của module auth (xem docs/ERD.md, nhóm "Người dùng và nhận diện")."""

from datetime import datetime

from sqlalchemy import BigInteger, CHAR, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Vai trò. Khách hàng và nhân viên dùng chung bảng users, phân biệt bằng role (ERD mục 8).
CUSTOMER = "customer"
ANALYST = "analyst"
RISK_MANAGER = "risk_manager"
ADMIN = "admin"
STAFF_ROLES = (ANALYST, RISK_MANAGER, ADMIN)
ALL_ROLES = (CUSTOMER, *STAFF_ROLES)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=CUSTOMER)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | locked
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Device(Base):
    """Một trình duyệt/thiết bị, nhận diện bằng ID ngẫu nhiên lưu trong trình duyệt.

    Đây KHÔNG phải fingerprint thật: người dùng xóa dữ liệu trình duyệt là có ID mới.
    Luật rủi ro coi đây là tín hiệu mạnh nhưng không tuyệt đối (RULES_V0, F02).
    """

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_uid: Mapped[str] = mapped_column(String(64), unique=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserDevice(Base):
    __tablename__ = "user_devices"
    __table_args__ = (Index("ix_user_devices_device_last_seen", "device_id", "last_seen_at"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserIp(Base):
    """IP từng dùng. Không lưu IP gốc: chỉ lưu bản băm (để đếm) và bản che (để hiển thị)."""

    __tablename__ = "user_ips"
    __table_args__ = (Index("ix_user_ips_ip_last_seen", "ip_hash", "last_seen_at"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    ip_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    ip_masked: Mapped[str] = mapped_column(String(64))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthSession(Base):
    """Phiên đăng nhập. Cookie chứa token ngẫu nhiên; CSDL chỉ lưu bản băm của token,
    nên lộ CSDL cũng không dùng lại được phiên. Đăng xuất = đánh dấu revoked_at."""

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
