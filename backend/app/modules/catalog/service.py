"""Logic của module catalog. Module khác (cart, order) lấy thông tin sản phẩm qua các hàm ở đây."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.search import LIKE_ESCAPE, contains_pattern
from app.modules.catalog.models import CATEGORIES, Product
from app.modules.catalog.schemas import CategoryOut, ProductOut, ProductPage


def _to_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        sku=p.sku,
        slug=p.slug,
        name=p.name,
        category=p.category,
        category_name=CATEGORIES.get(p.category, p.category),
        description=p.description,
        price=p.price,
        image_url=p.image_url,
        stock=p.stock,
        specs=p.specs or [],
    )


# Cách sắp xếp danh sách sản phẩm: mã trên URL -> thứ tự cột (luôn kèm id để thứ tự ổn định khi phân trang)
SORTS = {
    "new": (Product.created_at.desc(), Product.id.desc()),
    "price_asc": (Product.price.asc(), Product.id.asc()),
    "price_desc": (Product.price.desc(), Product.id.desc()),
}


def list_products(
    db: Session,
    *,
    q: str | None,
    category: str | None,
    page: int,
    page_size: int,
    sort: str = "new",
    min_price: int | None = None,
    max_price: int | None = None,
) -> ProductPage:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise AppError("INVALID_PRICE_RANGE", "Giá tối thiểu phải nhỏ hơn hoặc bằng giá tối đa.", 422)
    conditions = [Product.is_active.is_(True)]
    if category:
        conditions.append(Product.category == category)
    if q:
        # Tìm đơn giản theo tên hoặc mô tả
        pattern = contains_pattern(q)
        conditions.append(or_(Product.name.like(pattern, escape=LIKE_ESCAPE),
                              Product.description.like(pattern, escape=LIKE_ESCAPE)))
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)

    total = db.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    rows = db.scalars(
        select(Product)
        .where(*conditions)
        .order_by(*SORTS[sort])
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ProductPage(items=[_to_out(p) for p in rows], total=total, page=page, page_size=page_size)


def get_product_by_slug(db: Session, slug: str) -> ProductOut:
    product = db.scalar(select(Product).where(Product.slug == slug, Product.is_active.is_(True)))
    if product is None:
        raise AppError("PRODUCT_NOT_FOUND", "Không tìm thấy sản phẩm.", 404)
    return _to_out(product)


def get_active_products(db: Session, ids: list[int]) -> dict[int, ProductOut]:
    """Hàm công khai cho module khác (cart, order): lấy sản phẩm đang bán theo danh sách id."""
    if not ids:
        return {}
    rows = db.scalars(select(Product).where(Product.id.in_(ids), Product.is_active.is_(True))).all()
    return {p.id: _to_out(p) for p in rows}


def get_active_product(db: Session, product_id: int) -> ProductOut:
    product = get_active_products(db, [product_id]).get(product_id)
    if product is None:
        raise AppError("PRODUCT_NOT_FOUND", "Không tìm thấy sản phẩm.", 404)
    return product


def reserve_stock(db: Session, quantities: dict[int, int]) -> dict[int, ProductOut]:
    """Trừ tồn kho khi đặt hàng. Gọi BÊN TRONG transaction đặt hàng (chưa commit).

    SELECT ... FOR UPDATE khóa các dòng sản phẩm tới khi transaction kết thúc, nên hai đơn
    cùng mua món cuối cùng không thể cùng thành công. Khóa theo thứ tự id tăng dần để tránh deadlock.
    Trả về thông tin sản phẩm TẠI THỜI ĐIỂM đặt (để chụp giá vào đơn).
    """
    rows = db.scalars(
        select(Product).where(Product.id.in_(quantities)).order_by(Product.id).with_for_update()
    ).all()
    found = {p.id: p for p in rows}
    snapshot: dict[int, ProductOut] = {}
    for product_id, qty in quantities.items():
        p = found.get(product_id)
        if p is None or not p.is_active:
            raise AppError("PRODUCT_NOT_FOUND", "Có sản phẩm trong giỏ đã ngừng bán.", 409)
        if p.stock < qty:
            raise AppError("NOT_ENOUGH_STOCK", f"\"{p.name}\" chỉ còn {p.stock} sản phẩm.", 409)
        p.stock -= qty
        snapshot[product_id] = _to_out(p)
    return snapshot


def release_stock(db: Session, quantities: dict[int, int]) -> None:
    """Trả hàng về kho (ví dụ giao thất bại). Gọi bên trong transaction của bên gọi."""
    rows = db.scalars(
        select(Product).where(Product.id.in_(quantities)).order_by(Product.id).with_for_update()
    ).all()
    for p in rows:
        p.stock += quantities[p.id]


def list_categories(db: Session) -> list[CategoryOut]:
    counts = dict(
        db.execute(
            select(Product.category, func.count()).where(Product.is_active.is_(True)).group_by(Product.category)
        ).all()
    )
    return [CategoryOut(code=code, name=name, product_count=counts.get(code, 0)) for code, name in CATEGORIES.items()]
