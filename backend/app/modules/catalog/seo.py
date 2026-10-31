"""robots.txt và sitemap.xml cho máy tìm kiếm (SEO).

Không nằm dưới /api vì máy tìm kiếm luôn tìm hai file này ở gốc website. Khi chạy dev, Vite chuyển
tiếp /robots.txt và /sitemap.xml sang backend (frontend/vite.config.ts).
Sitemap chỉ liệt kê trang CÔNG KHAI: trang chủ, trang danh mục (/danh-muc/...), trang sản phẩm đang bán.
"""

from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.modules.catalog import service
from app.modules.catalog.models import Product

router = APIRouter(tags=["seo"], include_in_schema=False)

# Khu vực riêng tư hoặc không có nội dung cho máy tìm kiếm. Các trang này cũng gắn thẻ noindex ở frontend.
PRIVATE_PATHS = ["/api/", "/console", "/cart", "/checkout", "/orders", "/appeals", "/login", "/register"]


def _site_url() -> str:
    return get_settings().site_url.rstrip("/")


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt() -> str:
    lines = ["User-agent: *", *(f"Disallow: {p}" for p in PRIVATE_PATHS), "", f"Sitemap: {_site_url()}/sitemap.xml"]
    return "\n".join(lines) + "\n"


def sitemap_paths(db: Session) -> list[str]:
    paths = ["/", "/danh-muc"]
    paths += [f"/danh-muc/{c.code}" for c in service.list_categories(db) if c.product_count > 0]
    slugs = db.scalars(select(Product.slug).where(Product.is_active.is_(True)).order_by(Product.id)).all()
    paths += [f"/products/{s}" for s in slugs]
    return paths


@router.get("/sitemap.xml")
def sitemap_xml(db: Session = Depends(get_db)) -> Response:
    base = _site_url()
    urls = "".join(f"<url><loc>{escape(base + p)}</loc></url>" for p in sitemap_paths(db))
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    )
    return Response(content=body, media_type="application/xml")
