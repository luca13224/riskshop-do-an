from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import require_roles
from app.modules.auth.models import ADMIN, CUSTOMER, RISK_MANAGER, STAFF_ROLES, User
from app.modules.order import service
from app.modules.order.schemas import CheckoutIn, OrderOut, OrderSummaryOut, ShipmentUpdateIn, StaffOrderOut

router = APIRouter(tags=["order"])
customer = require_roles(CUSTOMER)


@router.post("/orders/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    data: CheckoutIn,
    response: Response,
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    user: User = Depends(customer),
    db: Session = Depends(get_db),
):
    order, created = service.checkout(db, user, data, idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK  # request lặp lại: trả đơn cũ, không tạo đơn mới
    return order


@router.get("/orders", response_model=list[OrderSummaryOut])
def my_orders(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.list_my_orders(db, user)


@router.get("/orders/{order_code}", response_model=OrderOut)
def my_order(order_code: str, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.get_order(db, user, order_code)


# ---------- Console ----------

@router.get("/console/orders", response_model=list[StaffOrderOut])
def recent_orders(_: User = Depends(require_roles(*STAFF_ROLES)), db: Session = Depends(get_db)):
    return service.list_recent_orders(db)


@router.post("/console/orders/{order_code}/shipment", response_model=StaffOrderOut)
def update_shipment(
    order_code: str,
    data: ShipmentUpdateIn,
    actor: User = Depends(require_roles(ADMIN, RISK_MANAGER)),
    db: Session = Depends(get_db),
):
    return service.update_shipment(db, actor, order_code, data.status, data.note)
