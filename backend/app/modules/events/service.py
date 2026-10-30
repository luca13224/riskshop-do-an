"""Ghi sự kiện hành vi. Bên gọi tự commit (sự kiện đi chung transaction với hành động của nó)."""

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import utcnow
from app.modules.auth.models import Device
from app.modules.auth.security import hash_ip
from app.modules.events.models import Event


def ensure_device_id(db: Session, device_uid: str | None) -> int | None:
    """Trả về id của thiết bị, tạo mới nếu chưa có. device_uid đã được kiểm tra định dạng ở tầng auth."""
    if not device_uid:
        return None
    db.execute(
        mysql_insert(Device)
        .values(device_uid=device_uid, first_seen_at=utcnow())
        .on_duplicate_key_update(device_uid=device_uid)
    )
    return db.scalar(select(Device.id).where(Device.device_uid == device_uid))


def record(
    db: Session,
    event_type: str,
    *,
    user_id: int | None,
    device_uid: str | None,
    ip: str | None,
    payload: dict | None = None,
) -> None:
    db.add(
        Event(
            event_type=event_type,
            user_id=user_id,
            device_id=ensure_device_id(db, device_uid),
            ip_hash=hash_ip(ip, get_settings().ip_hash_secret) if ip else None,
            payload=payload,
        )
    )
    db.flush()
