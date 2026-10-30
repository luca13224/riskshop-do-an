"""Dependency của FastAPI dùng chung: lấy người dùng hiện tại, kiểm tra vai trò, thông tin thiết bị/IP.

Cách dùng ở module khác:
    @router.get("/cases", dependencies=[Depends(require_roles(ANALYST, RISK_MANAGER))])
"""

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.modules.auth import service
from app.modules.auth.models import User

DEVICE_HEADER = "X-Device-Id"


def get_client_context(request: Request) -> service.ClientContext:
    return service.ClientContext(
        device_uid=service.normalize_device_uid(request.headers.get(DEVICE_HEADER)),
        ip=request.client.host if request.client else None,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(get_settings().session_cookie_name)
    user = service.get_user_by_token(db, token) if token else None
    if user is None:
        raise AppError("UNAUTHORIZED", "Bạn cần đăng nhập.", 401)
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Người dùng hiện tại nếu đã đăng nhập, ngược lại None (cho các trang công khai)."""
    token = request.cookies.get(get_settings().session_cookie_name)
    return service.get_user_by_token(db, token) if token else None


def require_roles(*roles: str) -> Callable[..., User]:
    """Chặn ở BACKEND: vai trò không nằm trong danh sách thì trả 403, dù frontend có ẩn nút hay không."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError("FORBIDDEN", "Bạn không có quyền thực hiện thao tác này.", 403)
        return user

    return checker
