from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


def record(
    db: Session,
    *,
    actor_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict | None = None,
    after: dict | None = None,
    note: str | None = None,
) -> None:
    """Ghi một dòng audit trong CÙNG transaction với thao tác (bên gọi commit).
    Thao tác thành công thì chắc chắn có audit; thao tác rollback thì audit cũng rollback."""
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id,
                    before_data=before, after_data=after, note=note))
