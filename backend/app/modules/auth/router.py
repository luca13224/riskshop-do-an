"""Endpoint của module auth: /api/auth/..."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.modules.auth import service
from app.modules.auth.deps import get_client_context, get_current_user, require_roles
from app.modules.auth.models import ADMIN, RISK_MANAGER, User
from app.modules.auth.schemas import ContactOut, LoginIn, RegisterIn, RevealContactIn, UserOut
from app.modules.promotion import seed as promotion_seed
from app.modules.promotion import service as promotion

router = APIRouter(prefix="/auth", tags=["auth"])
console_router = APIRouter(prefix="/console/users", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,  # JavaScript không đọc được cookie -> giảm thiệt hại nếu bị XSS
        samesite="lax",  # trang web khác không gửi kèm cookie khi gọi POST -> giảm CSRF
        secure=settings.cookie_secure,
        path="/",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterIn,
    response: Response,
    db: Session = Depends(get_db),
    ctx: service.ClientContext = Depends(get_client_context),
):
    user, token = service.register_customer(db, data, ctx)
    # Shop cấp sẵn mã người mới vào túi voucher (bộ luật v3)
    promotion.grant(db, user, promotion_seed.WELCOME_CODE)
    db.commit()
    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserOut)
def login(
    data: LoginIn,
    response: Response,
    db: Session = Depends(get_db),
    ctx: service.ClientContext = Depends(get_client_context),
):
    user, token = service.login(db, data.email, data.password, ctx)
    _set_session_cookie(response, token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    name = get_settings().session_cookie_name
    token = request.cookies.get(name)
    if token:
        service.logout(db, token)
    response.delete_cookie(name, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@console_router.post("/{user_id}/reveal-contact", response_model=ContactOut)
def reveal_contact(
    user_id: int,
    data: RevealContactIn,
    actor: User = Depends(require_roles(RISK_MANAGER, ADMIN)),  # analyst không cần liên hệ khách (least privilege)
    db: Session = Depends(get_db),
):
    return service.reveal_contact(db, actor, user_id, data.reason)
