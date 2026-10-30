"""Che dữ liệu cá nhân (PII) trước khi trả về Risk Console.

Che ở BACKEND chứ không ở frontend: nếu chỉ ẩn trên giao diện thì dữ liệu thật vẫn nằm trong response API.
Nhân viên cần xem đầy đủ thì gọi endpoint "xem liên hệ" (có lý do, có audit log).
"""

from typing import Annotated

from pydantic import PlainSerializer


def mask_email(email: str) -> str:
    """minh.nguyen@gmail.com -> mi***@gmail.com ; ab@x.vn -> a***@x.vn"""
    local, sep, domain = email.partition("@")
    if not sep:
        return "***"
    keep = 2 if len(local) > 3 else 1
    return f"{local[:keep]}***@{domain}"


def mask_phone(phone: str | None) -> str | None:
    """0912345678 -> 091****678"""
    if not phone:
        return phone
    return f"{phone[:3]}****{phone[-3:]}" if len(phone) > 6 else "***"


# Dùng làm kiểu cho field trong schema: giá trị vẫn là email thật trong Python, chỉ bị che khi xuất JSON
MaskedEmail = Annotated[str, PlainSerializer(mask_email, return_type=str, when_used="json")]
