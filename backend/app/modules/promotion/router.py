"""Túi voucher của khách (bộ luật v3)."""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import CUSTOMER, User
from app.modules.promotion import service
from app.modules.risk import service as risk

router = APIRouter(prefix="/vouchers", tags=["promotion"])


class WalletItemOut(BaseModel):
    code: str
    description: str
    min_order_value: int
    granted: bool  # được shop cấp riêng (khác mã công khai)
    status: Literal["usable", "used", "locked", "not_eligible"]


@router.get("/wallet", response_model=list[WalletItemOut])
def my_wallet(user: User = Depends(require_roles(CUSTOMER)), db: Session = Depends(get_db)):
    # Điểm tin cậy KHÔNG trả về cho khách (tránh bị dò ngưỡng); chỉ trả trạng thái từng mã
    return service.wallet(db, user, risk.latest_trust(db, user.id))
