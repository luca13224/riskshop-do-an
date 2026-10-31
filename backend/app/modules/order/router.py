from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import get_client_context, require_roles
from app.modules.auth.models import ADMIN, CUSTOMER, RISK_MANAGER, STAFF_ROLES, User
from app.modules.auth.service import ClientContext
from app.modules.order import models as m
from app.modules.order import service
from app.modules.order.schemas import (
    CheckoutIn,
    OrderOut,
    OrderSummaryOut,
    PaymentOptionsOut,
    ShipmentUpdateIn,
    StaffOrderOut,
    StaffOrderPage,
)

router = APIRouter(tags=["order"])
customer = require_roles(CUSTOMER)
STATUS_PATTERN = "^(" + "|".join(
    [m.PENDING_REVIEW, m.CONFIRMED, m.SHIPPING, m.DELIVERED, m.DELIVERY_FAILED, m.CANCELLED, m.REJECTED]
) + ")$"


@router.post("/orders/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    data: CheckoutIn,
    response: Response,
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
    user: User = Depends(customer),
    db: Session = Depends(get_db),
    client: ClientContext = Depends(get_client_context),
):
    order, created = service.checkout(db, user, data, idempotency_key, client)
    if not created:
        response.status_code = status.HTTP_200_OK  # request lặp lại: trả đơn cũ, không tạo đơn mới
    return order


@router.get("/orders/payment-options", response_model=PaymentOptionsOut)
def payment_options(
    user: User = Depends(customer),
    db: Session = Depends(get_db),
    client: ClientContext = Depends(get_client_context),
):
    # Khai báo TRƯỚC /orders/{order_code}, nếu không "payment-options" bị hiểu là một mã đơn
    return service.payment_options(db, user, client)


@router.get("/orders", response_model=list[OrderSummaryOut])
def my_orders(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.list_my_orders(db, user)


@router.get("/orders/{order_code}", response_model=OrderOut)
def my_order(order_code: str, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.get_order(db, user, order_code)


# ---------- Console ----------

@router.get("/console/orders", response_model=StaffOrderPage)
def staff_orders(
    status_filter: str | None = Query(default=None, alias="status", pattern=STATUS_PATTERN),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    query = q.strip() if q else ""
    return service.list_orders_for_staff(
        db, status=status_filter, q=query or None, page=page, page_size=page_size
    )


@router.post("/console/orders/{order_code}/shipment", response_model=StaffOrderOut)
def update_shipment(
    order_code: str,
    data: ShipmentUpdateIn,
    actor: User = Depends(require_roles(ADMIN, RISK_MANAGER)),
    db: Session = Depends(get_db),
):
    return service.update_shipment(db, actor, order_code, data.status, data.note)
