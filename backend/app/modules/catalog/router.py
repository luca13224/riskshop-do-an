"""Endpoint công khai của catalog: ai cũng xem được, không cần đăng nhập."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.catalog import service
from app.modules.catalog.models import CATEGORIES
from app.modules.catalog.schemas import CategoryOut, ProductOut, ProductPage

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=ProductPage)
def list_products(
    q: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, pattern="^(" + "|".join(CATEGORIES) + ")$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    db: Session = Depends(get_db),
):
    return service.list_products(db, q=q.strip() if q else None, category=category, page=page, page_size=page_size)


@router.get("/products/{slug}", response_model=ProductOut)
def get_product(slug: str, db: Session = Depends(get_db)):
    return service.get_product_by_slug(db, slug)


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return service.list_categories(db)
