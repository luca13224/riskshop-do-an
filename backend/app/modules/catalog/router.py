"""Endpoint công khai của catalog: ai cũng xem được, không cần đăng nhập."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.auth.deps import get_client_context, get_optional_user
from app.modules.auth.models import User
from app.modules.auth.service import ClientContext
from app.modules.catalog import service
from app.modules.events import service as events
from app.modules.events.models import PRODUCT_VIEW
from app.modules.catalog.models import CATEGORIES
from app.modules.catalog.schemas import CategoryOut, ProductOut, ProductPage

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=ProductPage)
def list_products(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, pattern="^(" + "|".join(CATEGORIES) + ")$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    sort: str = Query(default="new", pattern="^(" + "|".join(service.SORTS) + ")$"),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_products(
        db, q=q.strip() if q else None, category=category, page=page, page_size=page_size,
        sort=sort, min_price=min_price, max_price=max_price,
    )


@router.get("/products/{slug}", response_model=ProductOut)
def get_product(
    slug: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    ctx: ClientContext = Depends(get_client_context),
):
    product = service.get_product_by_slug(db, slug)
    # Ghi lượt xem sản phẩm (đặc trưng F06: người thật thường xem sản phẩm trước khi mua)
    events.record(
        db, PRODUCT_VIEW, user_id=user.id if user else None, device_uid=ctx.device_uid, ip=ctx.ip,
        payload={"product_id": product.id},
    )
    db.commit()
    return product


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)
