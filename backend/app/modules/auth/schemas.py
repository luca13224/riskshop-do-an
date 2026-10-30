"""Dữ liệu vào/ra API của module auth."""

import re

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^0\d{9}$")  # số di động Việt Nam 10 chữ số


def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Email không hợp lệ")
    return value


class RegisterIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    phone: str | None = None

    _email = field_validator("email")(_normalize_email)

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Họ tên không được để trống")
        return value

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        value = value.strip().replace(" ", "")
        if not _PHONE_RE.match(value):
            raise ValueError("Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")
        return value


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)

    _email = field_validator("email")(_normalize_email)


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str | None
    role: str

    model_config = {"from_attributes": True}
