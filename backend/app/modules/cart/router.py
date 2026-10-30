"""Endpoint giỏ hàng: /api/cart/... Chỉ khách hàng đã đăng nhập mới có giỏ."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import get_client_context, require_roles
from app.modules.auth.service import ClientContext
from app.modules.auth.models import CUSTOMER, User
from app.modules.cart import service
from app.modules.cart.schemas import AddItemIn, ApplyVoucherIn, CartOut, UpdateItemIn

router = APIRouter(prefix="/cart", tags=["cart"])
customer = require_roles(CUSTOMER)


@router.get("", response_model=CartOut)
def get_cart(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.view_cart(db, user)


@router.post("/items", response_model=CartOut)
def add_item(data: AddItemIn, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.add_item(db, user, data.product_id, data.quantity)


@router.patch("/items/{product_id}", response_model=CartOut)
def update_item(product_id: int, data: UpdateItemIn, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.update_item(db, user, product_id, data.quantity)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(product_id: int, user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.remove_item(db, user, product_id)


@router.post("/voucher", response_model=CartOut)
def apply_voucher(
    data: ApplyVoucherIn,
    user: User = Depends(customer),
    db: Session = Depends(get_db),
    client: ClientContext = Depends(get_client_context),
):
    return service.apply_voucher(db, user, data.code, client)


@router.delete("/voucher", response_model=CartOut)
def remove_voucher(user: User = Depends(customer), db: Session = Depends(get_db)):
    return service.remove_voucher(db, user)
