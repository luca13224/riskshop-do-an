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

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.search import LIKE_ESCAPE, contains_pattern
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.auth.service import ClientContext
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
    StaffOrderPage,
)
from app.modules.promotion import service as promotion
from app.modules.risk import service as risk
from app.modules.risk.models import PAYMENT_OPTIONS, PLACE_ORDER

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


def address_hash(a: AddressIn) -> str:
    return hashlib.sha256(normalize_address(a).encode()).hexdigest()


def _save_address(db: Session, user: User, a: AddressIn) -> int:
    norm_hash = address_hash(a)
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


def checkout(
    db: Session, user: User, data: CheckoutIn, idempotency_key: str, client: ClientContext
) -> tuple[OrderOut, bool]:
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
        # Lưu địa chỉ TRƯỚC khi chấm điểm, để đặc trưng F03 (tài khoản chung địa chỉ) tính cả đơn này
        address_id = _save_address(db, user, data.address)

        # ---- Risk Engine, context place_order: lớp bảo vệ cuối, luôn chạy ở server ----
        result = risk.evaluate(db, risk.EvaluationRequest(
            context=PLACE_ORDER, user=user, client=client, order_value=subtotal - discount,
            voucher_code=applied.code if applied else None,
            voucher_new_user=applied.new_user_only if applied else None,
            payment_method=data.payment_method, address_hash=address_hash(data.address),
        ))
        actions = result.actions
        if actions["block"] or actions["disable_cod"] or actions["remove_voucher"]:
            # Không tạo đơn: hoàn tác giữ chỗ tồn kho..., nhưng VẪN lưu quyết định để truy vết
            db.rollback()
            if actions["remove_voucher"]:
                cart.drop_voucher(db, user)
            risk.record(db, result)
            db.commit()
            if actions["block"]:
                raise AppError("ORDER_BLOCKED", result.customer_message, 403)
            code = "VOUCHER_NOT_APPLICABLE" if actions["remove_voucher"] else "COD_NOT_AVAILABLE"
            raise AppError(code, result.customer_message, 409)
        status = m.PENDING_REVIEW if actions["hold_order"] else m.CONFIRMED

        order = m.Order(
            order_code=_new_order_code(),
            user_id=user.id,
            address_id=address_id,
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
        risk.record(db, result, order_id=order.id)
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


def payment_options(db: Session, user: User, client: ClientContext) -> dict:
    """Risk Engine, context payment_options: có cho thanh toán COD với giỏ hiện tại không.

    Chỉ để giao diện ẩn nút COD cho đẹp; lớp chặn thật vẫn là lần chấm điểm lúc đặt hàng.
    """
    quantities, voucher_id = cart.get_checkout_snapshot(db, user)
    products = catalog.get_active_products(db, list(quantities))
    subtotal = sum(products[pid].price * qty for pid, qty in quantities.items() if pid in products)
    result = risk.evaluate(db, risk.EvaluationRequest(
        context=PAYMENT_OPTIONS, user=user, client=client, order_value=subtotal, payment_method=m.COD,
    ))
    risk.record(db, result)
    db.commit()
    cod_allowed = not result.actions["disable_cod"]
    return {"cod_allowed": cod_allowed, "message": None if cod_allowed else result.customer_message}


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

def list_orders_for_staff(
    db: Session, *, status: str | None = None, q: str | None = None, page: int = 1, page_size: int = 20
) -> StaffOrderPage:
    """Danh sách đơn cho Console: lọc theo trạng thái, tìm theo mã đơn / email / tên khách, mới nhất trước.
    Email trong kết quả vẫn được che (MaskedEmail): tìm theo email thì nhân viên phải biết trước email đó."""
    conditions = []
    if q:
        pattern = contains_pattern(q)
        conditions.append(or_(
            m.Order.order_code.like(pattern, escape=LIKE_ESCAPE),
            User.email.like(pattern, escape=LIKE_ESCAPE),
            User.full_name.like(pattern, escape=LIKE_ESCAPE),
        ))
    # Đếm theo trạng thái TRƯỚC khi áp bộ lọc trạng thái, để chip nào cũng hiện đúng con số của nó
    status_counts = dict(db.execute(
        select(m.Order.status, func.count()).join(User, User.id == m.Order.user_id)
        .where(*conditions).group_by(m.Order.status)
    ).all())
    if status:
        conditions.append(m.Order.status == status)
    total = db.scalar(
        select(func.count()).select_from(m.Order).join(User, User.id == m.Order.user_id).where(*conditions)
    ) or 0
    rows = db.execute(
        select(m.Order, User.email, User.full_name)
        .join(User, User.id == m.Order.user_id)
        .where(*conditions)
        .order_by(m.Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    counts = _item_counts(db, [o.id for o, _, _ in rows])
    items = [
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
    return StaffOrderPage(items=items, total=total, page=page, page_size=page_size, status_counts=status_counts)


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


# ---------- Dành cho module cases ----------

def order_brief(db: Session, order_id: int) -> dict | None:
    """Hàm công khai: thông tin ngắn của một đơn (hiển thị trong case)."""
    order = db.get(m.Order, order_id)
    if order is None:
        return None
    address = db.get(m.Address, order.address_id)
    return {
        "order_code": order.order_code,
        "status": order.status,
        "payment_method": order.payment_method,
        "total": order.total,
        "created_at": order.created_at,
        # Nhân viên xem case chỉ thấy khu vực giao hàng, không thấy số nhà (tối thiểu hóa dữ liệu cá nhân)
        "area": f"{address.ward}, {address.district}, {address.province}" if address else "",
    }


def resolve_review(db: Session, order_id: int, approve: bool, actor_id: int, note: str) -> str | None:
    """Duyệt hoặc từ chối đơn đang chờ xác minh. Bên gọi commit. Trả về trạng thái mới (None nếu không đổi).

    Từ chối thì hoàn hàng về kho. Chỉ đơn đang PENDING_REVIEW mới được xử lý.
    """
    order = db.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
    if order is None or order.status != m.PENDING_REVIEW:
        return None
    order.status = m.CONFIRMED if approve else m.REJECTED
    if not approve:
        items = db.scalars(select(m.OrderItem).where(m.OrderItem.order_id == order.id)).all()
        catalog.release_stock(db, {i.product_id: i.quantity for i in items})
    db.add(m.ShipmentEvent(order_id=order.id, status=order.status, note=note[:255], actor_id=actor_id))
    return order.status
