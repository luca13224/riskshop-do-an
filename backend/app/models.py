"""Nạp model của mọi module vào một chỗ, để Alembic autogenerate nhìn thấy đủ bảng.

Mỗi khi tạo module có models.py mới, thêm một dòng import vào đây, ví dụ:
    from app.modules.auth import models as auth_models  # noqa: F401
"""
