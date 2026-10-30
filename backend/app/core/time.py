from datetime import UTC, datetime


def utcnow() -> datetime:
    """Thời điểm hiện tại theo UTC, dạng không kèm múi giờ (MariaDB DATETIME không lưu múi giờ).

    Quy ước toàn dự án: CSDL luôn lưu UTC; chỉ đổi sang giờ Việt Nam khi hiển thị.
    """
    return datetime.now(UTC).replace(tzinfo=None)
