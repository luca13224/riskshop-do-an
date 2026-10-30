"""Đặt hàng (checkout), xem đơn, cập nhật giao hàng.

Checkout là luồng quan trọng nhất, chạy trong MỘT transaction:
  giữ chỗ tồn kho (khóa dòng) -> kiểm tra lại voucher -> tạo đơn -> ghi lượt voucher -> làm trống giỏ.
Bất kỳ bước nào lỗi thì rollback toàn bộ: không trừ kho, không mất lượt voucher, giỏ còn nguyên.
"""

import hashlib
import re
import secrets
import string
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.cart import service as cart
from app.modules.catalog import service as catalog
from app.modules.order import models as m
from app.modules.order.schemas import (
    AddressIn,
    CheckoutIn,
    OrderItemOut,
    OrderOut,
    OrderSummaryOut,
    ShipmentEventOut,
    StaffOrderOut,
)
from app.modules.promotion import service as promotion

IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")

# Chuyển trạng thái giao hàng hợp lệ (máy trạng thái)
SHIPMENT_TRANSITIONS = {
    m.CONFIRMED: {m.SHIPPING},
    m.SHIPPING: {m.DELIVERED, m.DELIVERY_FAILED},
}


# ---------- Địa chỉ ----------

def normalize_address(a: AddressIn) -> str:
    """Chuẩn hóa để so khớp: bỏ dấu, chữ thường, bỏ ký tự đặc biệt, "số 05" -> "5"."""
    raw = "|".join([a.line, a.ward, a.district, a.province])
    raw = raw.replace("đ", "d").replace("Đ", "D")
    raw = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode().lower()
    raw = re.sub(r"\b(p|q)\.?(?=\d)", " ", raw)  # "Q1", "P.12" viết liền với số
    raw = re.sub(r"\b(so|duong|phuong|quan|huyen|xa|tinh|thanh pho|tp|p|q)\b\.?", " ", raw)
    raw = re.sub(r"\b0+(\d)", r"\1", raw)  # 05 -> 5
    raw = re.sub(r"[^a-z0-9|]+", " ", raw)
    return "|".join(" ".join(part.split()) for part in raw.split("|"))


def _save_address(db: Session, user: User, a: AddressIn) -> int:
    norm_hash = hashlib.sha256(normalize_address(a).encode()).hexdigest()
    db.execute(
        mysql_insert(m.Address)
        .values(user_id=user.id, norm_hash=norm_hash, created_at=utcnow(), **a.model_dump())
        # Cùng người, cùng địa chỉ (sau chuẩn hóa): cập nhật tên/SĐT người nhận, không tạo dòng mới
        .on_duplicate_key_update(recipient_name=a.recipient_name, phone=a.phone)
    )
    return db.scalar(select(m.Address.id).where(m.Address.user_id == user.id, m.Address.norm_hash == norm_hash))


# ---------- Checkout ----------

def _new_order_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "RS" + utcnow().strftime("%y%m%d") + "".join(secrets.choice(alphabet) for _ in range(6))


def checkout(db: Session, user: User, data: CheckoutIn, idempotency_key: str) -> tuple[OrderOut, bool]:
    """Trả về (đơn, created). created=False nghĩa là request lặp lại (cùng Idempotency-Key)."""
    if not IDEMPOTENCY_RE.match(idempotency_key or ""):
        raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Thiếu hoặc sai định dạng Idempotency-Key.", 400)

    existing = _find_by_key(db, user, idempotency_key)
    if existing:
        return get_order(db, user, existing.order_code), False

    quantities, voucher_id = cart.get_checkout_snapshot(db, user)
    if not quantities:
        raise AppError("CART_EMPTY", "Giỏ hàng đang trống.", 409)

    try:
        products = catalog.reserve_stock(db, quantities)
        subtotal = sum(products[pid].price * qty for pid, qty in quantities.items())

        applied = None
        if voucher_id is not None:
            # Kiểm tra lại: từ lúc áp mã tới lúc đặt hàng, voucher có thể đã hết hạn/hết lượt
            applied = promotion.validate(db, promotion.get_voucher(db, voucher_id), user, subtotal)
        discount = applied.discount if applied else 0

        # Chỗ nối Risk Engine (context place_order) sẽ đặt ở đây khi làm module risk:
        # quyết định có thể là REVIEW (status = PENDING_REVIEW), từ chối COD, hoặc BLOCK.
        status = m.CONFIRMED

        order = m.Order(
            order_code=_new_order_code(),
            user_id=user.id,
            address_id=_save_address(db, user, data.address),
            status=status,
            payment_method=data.payment_method,
            # Trả trước: cổng thanh toán là giả lập (sandbox), coi như đã thanh toán ngay
            payment_status="PAID" if data.payment_method == m.PREPAID else "UNPAID",
            subtotal=subtotal,
            discount=discount,
            total=subtotal - discount,
            voucher_code=applied.code if applied else None,
            idempotency_key=idempotency_key,
        )
        db.add(order)
        db.flush()
        for pid, qty in quantities.items():
            p = products[pid]
            db.add(
                m.OrderItem(
                    order_id=order.id,
                    product_id=pid,
                    product_name=p.name,
                    category=p.category,
                    unit_price=p.price,
                    quantity=qty,
                )
            )
        if applied:
            promotion.redeem(db, applied, user, order.id)
        cart.clear_cart(db, user)
        db.commit()
    except AppError:
        db.rollback()
        raise
    except IntegrityError:
        # Hai request cùng Idempotency-Key đến cùng lúc: request thua trả về đơn của request thắng
        db.rollback()
        existing = _find_by_key(db, user, idempotency_key)
        if existing:
            return get_order(db, user, existing.order_code), False
        raise
    return get_order(db, user, order.order_code), True


def _find_by_key(db: Session, user: User, key: str) -> m.Order | None:
    return db.scalar(select(m.Order).where(m.Order.user_id == user.id, m.Order.idempotency_key == key))


# ---------- Xem đơn ----------

def _to_out(db: Session, order: m.Order) -> OrderOut:
    items = db.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order.id).order_by(m.OrderItem.id)).all()
    address = db.get(m.Address, order.address_id)
    events = db.scalars(
        select(m.ShipmentEvent).where(m.ShipmentEvent.order_id == order.id).order_by(m.ShipmentEvent.id)
    ).all()
    return OrderOut(
        order_code=order.order_code,
        status=order.status,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        subtotal=order.subtotal,
        discount=order.discount,
        total=order.total,
        voucher_code=order.voucher_code,
        created_at=order.created_at,
        items=[
            OrderItemOut(
                product_id=i.product_id,
                product_name=i.product_name,
                category=i.category,
                unit_price=i.unit_price,
                quantity=i.quantity,
                line_total=i.unit_price * i.quantity,
            )
            for i in items
        ],
        address=AddressIn(
            recipient_name=address.recipient_name,
            phone=address.phone,
            line=address.line,
            ward=address.ward,
            district=address.district,
            province=address.province,
        ),
        events=[ShipmentEventOut(status=e.status, note=e.note, occurred_at=e.occurred_at) for e in events],
    )


def get_order(db: Session, user: User, order_code: str) -> OrderOut:
    order = db.scalar(select(m.Order).where(m.Order.order_code == order_code, m.Order.user_id == user.id))
    if order is None:
        # Đơn của người khác cũng trả 404 (không lộ là mã đơn đó có tồn tại)
        raise AppError("ORDER_NOT_FOUND", "Không tìm thấy đơn hàng.", 404)
    return _to_out(db, order)


def _item_counts(db: Session, order_ids: list[int]) -> dict[int, int]:
    if not order_ids:
        return {}
    return dict(
        db.execute(
            select(m.OrderItem.order_id, func.sum(m.OrderItem.quantity))
            .where(m.OrderItem.order_id.in_(order_ids))
            .group_by(m.OrderItem.order_id)
        ).all()
    )


def list_my_orders(db: Session, user: User) -> list[OrderSummaryOut]:
    orders = db.scalars(
        select(m.Order).where(m.Order.user_id == user.id).order_by(m.Order.id.desc()).limit(50)
    ).all()
    counts = _item_counts(db, [o.id for o in orders])
    return [
        OrderSummaryOut(
            order_code=o.order_code,
            status=o.status,
            payment_method=o.payment_method,
            total=o.total,
            item_count=int(counts.get(o.id, 0)),
            created_at=o.created_at,
        )
        for o in orders
    ]


# ---------- Dành cho nhân viên ----------

def list_recent_orders(db: Session, limit: int = 50) -> list[StaffOrderOut]:
    rows = db.execute(
        select(m.Order, User.email, User.full_name)
        .join(User, User.id == m.Order.user_id)
        .order_by(m.Order.id.desc())
        .limit(limit)
    ).all()
    counts = _item_counts(db, [o.id for o, _, _ in rows])
    return [
        StaffOrderOut(
            order_code=o.order_code,
            status=o.status,
            payment_method=o.payment_method,
            total=o.total,
            item_count=int(counts.get(o.id, 0)),
            created_at=o.created_at,
            customer_email=email,
            customer_name=name,
        )
        for o, email, name in rows
    ]


def update_shipment(db: Session, actor: User, order_code: str, new_status: str, note: str) -> StaffOrderOut:
    """Giả lập đơn vị vận chuyển. Giao thất bại thì trả hàng về kho.

    Đây là nguồn "nhãn" cho luật COD: tỷ lệ giao thất bại của từng khách (R07).
    """
    order = db.scalar(select(m.Order).where(m.Order.order_code == order_code).with_for_update())
    if order is None:
        raise AppError("ORDER_NOT_FOUND", "Không tìm thấy đơn hàng.", 404)
    if new_status not in SHIPMENT_TRANSITIONS.get(order.status, set()):
        raise AppError(
            "INVALID_TRANSITION", f"Không thể chuyển đơn từ {order.status} sang {new_status}.", 409
        )
    order.status = new_status
    if new_status == m.DELIVERED and order.payment_method == m.COD:
        order.payment_status = "PAID"  # COD: thu tiền khi giao thành công
    if new_status == m.DELIVERY_FAILED:
        items = db.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order.id)).all()
        catalog.release_stock(db, {i.product_id: i.quantity for i in items})
    db.add(m.ShipmentEvent(order_id=order.id, status=new_status, note=note, actor_id=actor.id))
    db.commit()
    owner = db.get(User, order.user_id)
    return StaffOrderOut(
        order_code=order.order_code,
        status=order.status,
        payment_method=order.payment_method,
        total=order.total,
        item_count=int(_item_counts(db, [order.id]).get(order.id, 0)),
        created_at=order.created_at,
        customer_email=owner.email,
        customer_name=owner.full_name,
    )
