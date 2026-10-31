"""Logic giỏ hàng.

Giá trong giỏ luôn là giá HIỆN TẠI của sản phẩm; chỉ khi đặt hàng mới "chụp" giá vào đơn.
Voucher trong giỏ được kiểm tra lại mỗi lần xem giỏ: hết điều kiện thì tự gỡ và báo cho khách.
"""

from sqlalchemy import delete, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.auth.models import User
from app.modules.auth.service import ClientContext
from app.modules.events import service as events
from app.modules.events.models import VOUCHER_ATTEMPT
from app.modules.risk import service as risk
from app.modules.risk.models import VOUCHER_APPLY
from app.modules.cart.models import Cart, CartItem
from app.modules.cart.schemas import CartItemOut, CartOut, CartVoucherOut
from app.modules.catalog import service as catalog
from app.modules.catalog.schemas import ProductOut
from app.modules.promotion import service as promotion

MAX_QTY_PER_ITEM = 99


def _get_or_create_cart(db: Session, user: User) -> Cart:
    # INSERT IGNORE theo UNIQUE(user_id): an toàn khi hai request tạo giỏ cùng lúc
    db.execute(mysql_insert(Cart).values(user_id=user.id).prefix_with("IGNORE"))
    return db.scalar(select(Cart).where(Cart.user_id == user.id))


def _check_stock(product: ProductOut, quantity: int) -> None:
    if product.stock <= 0:
        raise AppError("OUT_OF_STOCK", "Sản phẩm đã hết hàng.", 409)
    if quantity > product.stock:
        raise AppError("NOT_ENOUGH_STOCK", f"Chỉ còn {product.stock} sản phẩm.", 409)


def add_item(db: Session, user: User, product_id: int, quantity: int) -> CartOut:
    cart = _get_or_create_cart(db, user)
    product = catalog.get_active_product(db, product_id)
    item = db.get(CartItem, (cart.id, product_id))
    new_qty = (item.quantity if item else 0) + quantity
    if new_qty > MAX_QTY_PER_ITEM:
        raise AppError("QUANTITY_LIMIT", f"Mỗi sản phẩm tối đa {MAX_QTY_PER_ITEM} cái.", 409)
    _check_stock(product, new_qty)
    if item:
        item.quantity = new_qty
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=new_qty))
    db.commit()
    return view_cart(db, user)


def update_item(db: Session, user: User, product_id: int, quantity: int) -> CartOut:
    cart = _get_or_create_cart(db, user)
    item = db.get(CartItem, (cart.id, product_id))
    if item is None:
        raise AppError("CART_ITEM_NOT_FOUND", "Sản phẩm không có trong giỏ.", 404)
    _check_stock(catalog.get_active_product(db, product_id), quantity)
    item.quantity = quantity
    db.commit()
    return view_cart(db, user)


def remove_item(db: Session, user: User, product_id: int) -> CartOut:
    cart = _get_or_create_cart(db, user)
    db.execute(delete(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id))
    db.commit()
    return view_cart(db, user)


def apply_voucher(db: Session, user: User, code: str, client: ClientContext) -> CartOut:
    cart = _get_or_create_cart(db, user)
    items, subtotal = _load_items(db, cart)
    if not items:
        raise AppError("CART_EMPTY", "Giỏ hàng đang trống.", 409)

    # Ghi lần thử (kể cả mã sai) và commit ngay: đây là đặc trưng F05 cho luật R05 "thử mã liên tục"
    events.record(db, VOUCHER_ATTEMPT, user_id=user.id, device_uid=client.device_uid, ip=client.ip,
                  payload={"code": promotion.normalize_code(code)})
    db.commit()

    voucher = promotion.find_voucher(db, code)
    applied = promotion.validate(db, voucher, user, subtotal)  # luật NGHIỆP VỤ: sai điều kiện -> AppError

    if applied.risk_checked:
        # Luật RỦI RO (context voucher_apply)
        result = risk.evaluate(db, risk.EvaluationRequest(
            context=VOUCHER_APPLY, user=user, client=client, order_value=subtotal,
            voucher_code=applied.code, voucher_new_user=applied.new_user_only,
            voucher_min_trust=applied.min_trust,
        ))
        risk.record(db, result)
        if result.actions["remove_voucher"]:
            db.commit()
            # Thông điệp chung chung: không nói luật nào khớp, để kẻ gian không học được luật
            raise AppError("VOUCHER_NOT_APPLICABLE", result.customer_message, 409)

    cart.voucher_id = applied.id
    db.commit()
    return view_cart(db, user)


def drop_voucher(db: Session, user: User) -> None:
    """Gỡ voucher khỏi giỏ (Risk Engine yêu cầu lúc đặt hàng). Bên gọi commit."""
    _get_or_create_cart(db, user).voucher_id = None


def remove_voucher(db: Session, user: User) -> CartOut:
    cart = _get_or_create_cart(db, user)
    cart.voucher_id = None
    db.commit()
    return view_cart(db, user)


def get_checkout_snapshot(db: Session, user: User) -> tuple[dict[int, int], int | None]:
    """Hàm công khai cho module order: {product_id: số lượng} và voucher_id đang áp."""
    cart = _get_or_create_cart(db, user)
    rows = db.scalars(select(CartItem).where(CartItem.cart_id == cart.id)).all()
    return {ci.product_id: ci.quantity for ci in rows}, cart.voucher_id


def clear_cart(db: Session, user: User) -> None:
    """Làm trống giỏ sau khi đặt hàng. Gọi bên trong transaction đặt hàng (không commit)."""
    cart = _get_or_create_cart(db, user)
    db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    cart.voucher_id = None


def view_cart(db: Session, user: User) -> CartOut:
    cart = _get_or_create_cart(db, user)
    items, subtotal = _load_items(db, cart)

    applied = None
    notice = None
    if cart.voucher_id is not None:
        voucher = promotion.get_voucher(db, cart.voucher_id)
        try:
            if not items:
                raise AppError("CART_EMPTY", "Giỏ hàng đang trống.", 409)
            applied = promotion.validate(db, voucher, user, subtotal)
        except AppError as err:
            # Giỏ thay đổi làm voucher không còn hợp lệ: tự gỡ và giải thích cho khách
            cart.voucher_id = None
            if items:
                notice = f"Đã gỡ mã {voucher.code if voucher else ''}: {err.message}"
    db.commit()

    discount = applied.discount if applied else 0
    return CartOut(
        items=items,
        item_count=sum(i.quantity for i in items),
        subtotal=subtotal,
        discount=discount,
        total=subtotal - discount,
        voucher=CartVoucherOut(code=applied.code, description=applied.description, discount=discount)
        if applied
        else None,
        notice=notice,
    )


def _load_items(db: Session, cart: Cart) -> tuple[list[CartItemOut], int]:
    rows = db.scalars(select(CartItem).where(CartItem.cart_id == cart.id).order_by(CartItem.added_at)).all()
    products = catalog.get_active_products(db, [ci.product_id for ci in rows])
    items = []
    for ci in rows:
        p = products.get(ci.product_id)
        if p is None:
            # Sản phẩm đã ngừng bán: bỏ khỏi giỏ
            db.delete(ci)
            continue
        items.append(
            CartItemOut(
                product_id=p.id,
                slug=p.slug,
                name=p.name,
                category=p.category,
                image_url=p.image_url,
                unit_price=p.price,
                quantity=ci.quantity,
                stock=p.stock,
                line_total=p.price * ci.quantity,
            )
        )
    return items, sum(i.line_total for i in items)
