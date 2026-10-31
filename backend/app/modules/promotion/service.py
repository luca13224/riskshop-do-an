"""Kiểm tra điều kiện voucher và tính tiền giảm.

Đây là luật NGHIỆP VỤ (voucher có tồn tại, còn hạn, đủ giá trị tối thiểu, đúng đối tượng...).
Voucher sai nghiệp vụ bị từ chối ngay, không cần chấm điểm rủi ro (RULES_V0, mục 1).
"""

from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.promotion.models import PERCENT, UserVoucher, Voucher, VoucherRedemption

# Voucher tân thủ: chỉ cho tài khoản tạo trong vòng N ngày
NEW_USER_WINDOW_DAYS = 30


@dataclass(frozen=True)
class AppliedVoucher:
    id: int
    code: str
    description: str
    discount: int
    risk_checked: bool
    new_user_only: bool
    min_trust: int | None = None


def normalize_code(code: str) -> str:
    return code.strip().upper()


def find_voucher(db: Session, code: str) -> Voucher | None:
    return db.scalar(select(Voucher).where(func.upper(Voucher.code) == normalize_code(code)))


def get_voucher(db: Session, voucher_id: int) -> Voucher | None:
    return db.get(Voucher, voucher_id)


def compute_discount(voucher: Voucher, subtotal: int) -> int:
    if voucher.discount_type == PERCENT:
        discount = subtotal * voucher.amount // 100
        if voucher.max_discount is not None:
            discount = min(discount, voucher.max_discount)
    else:
        discount = voucher.amount
    return max(0, min(discount, subtotal))  # không bao giờ giảm quá tổng tiền


def validate(db: Session, voucher: Voucher | None, user: User, subtotal: int) -> AppliedVoucher:
    """Kiểm tra voucher cho giỏ hàng hiện tại. Sai điều kiện nào thì báo lỗi rõ ràng điều kiện đó."""
    now = utcnow()
    if voucher is None or not voucher.is_active:
        raise AppError("VOUCHER_NOT_FOUND", "Mã giảm giá không tồn tại.", 404)
    if voucher.starts_at and now < voucher.starts_at:
        raise AppError("VOUCHER_NOT_STARTED", "Mã giảm giá chưa đến thời gian áp dụng.", 409)
    if voucher.ends_at and now >= voucher.ends_at:
        raise AppError("VOUCHER_EXPIRED", "Mã giảm giá đã hết hạn.", 409)
    if voucher.max_redemptions is not None and voucher.redeemed_count >= voucher.max_redemptions:
        raise AppError("VOUCHER_EXHAUSTED", "Mã giảm giá đã hết lượt sử dụng.", 409)
    if db.scalar(
        select(VoucherRedemption.id).where(
            VoucherRedemption.voucher_id == voucher.id, VoucherRedemption.user_id == user.id
        )
    ):
        raise AppError("VOUCHER_ALREADY_USED", "Bạn đã dùng mã này rồi.", 409)
    if voucher.new_user_only and user.created_at < now - timedelta(days=NEW_USER_WINDOW_DAYS):
        raise AppError("VOUCHER_NEW_USER_ONLY", "Mã này chỉ dành cho thành viên mới.", 409)
    if subtotal < voucher.min_order_value:
        raise AppError(
            "VOUCHER_MIN_ORDER",
            f"Đơn hàng cần tối thiểu {voucher.min_order_value:,}đ để dùng mã này.".replace(",", "."),
            409,
        )
    return AppliedVoucher(
        id=voucher.id,
        code=voucher.code,
        description=voucher.description,
        discount=compute_discount(voucher, subtotal),
        risk_checked=voucher.risk_checked,
        new_user_only=voucher.new_user_only,
        min_trust=voucher.min_trust,
    )


def redeem(db: Session, applied: AppliedVoucher, user: User, order_id: int) -> None:
    """Ghi một lượt dùng voucher. Gọi BÊN TRONG transaction đặt hàng (chưa commit).

    Hai hàng rào chống race condition, đều nằm ở CSDL:
    1. UPDATE có điều kiện "còn lượt": MariaDB khóa dòng voucher, nên hai đơn đến cùng lúc
       không thể cùng lấy lượt cuối. Không dòng nào bị cập nhật nghĩa là đã hết lượt.
    2. UNIQUE(voucher_id, user_id): một người không dùng một mã hai lần.
    """
    result = db.execute(
        update(Voucher)
        .where(
            Voucher.id == applied.id,
            (Voucher.max_redemptions.is_(None)) | (Voucher.redeemed_count < Voucher.max_redemptions),
        )
        .values(redeemed_count=Voucher.redeemed_count + 1)
    )
    if result.rowcount != 1:
        raise AppError("VOUCHER_EXHAUSTED", "Mã giảm giá vừa hết lượt sử dụng.", 409)
    db.add(
        VoucherRedemption(
            voucher_id=applied.id, user_id=user.id, order_id=order_id, discount_amount=applied.discount
        )
    )
    try:
        db.flush()
    except IntegrityError as exc:
        raise AppError("VOUCHER_ALREADY_USED", "Bạn đã dùng mã này rồi.", 409) from exc


# ---------- Túi voucher (bộ luật v3) ----------

def grant(db: Session, user: User, code: str, source: str = "signup") -> None:
    """Cấp một mã vào túi voucher của tài khoản. Mã không tồn tại hoặc đã cấp rồi thì bỏ qua. Bên gọi commit."""
    voucher = find_voucher(db, code)
    if voucher is None or not voucher.is_active:
        return
    exists = db.scalar(select(UserVoucher.id).where(UserVoucher.user_id == user.id,
                                                    UserVoucher.voucher_id == voucher.id))
    if not exists:
        db.add(UserVoucher(user_id=user.id, voucher_id=voucher.id, source=source))


# Trạng thái hiển thị trong túi voucher. Thông điệp chung chung: không nói điểm tin cậy hay luật.
USABLE, USED, LOCKED, NOT_ELIGIBLE = "usable", "used", "locked", "not_eligible"


def wallet(db: Session, user: User, trust: int | None) -> list[dict]:
    """Mã được cấp riêng cho tài khoản + mã công khai đang chạy, kèm trạng thái.

    trust: điểm tin cậy gần nhất của tài khoản (None = chưa có, coi như đủ). Mã có min_trust cao hơn trust
    thì "tạm chưa áp dụng": đây là cách danh sách mã co lại dần khi tài khoản có dấu hiệu bất thường.
    """
    now = utcnow()
    granted = set(db.scalars(select(UserVoucher.voucher_id).where(UserVoucher.user_id == user.id)))
    used = set(db.scalars(select(VoucherRedemption.voucher_id).where(VoucherRedemption.user_id == user.id)))
    vouchers = db.scalars(select(Voucher).where(Voucher.is_active.is_(True)).order_by(Voucher.id)).all()
    items = []
    for v in vouchers:
        # Mã dành cho người mới chỉ hiện nếu được cấp vào túi; mã công khai thì ai cũng thấy
        if v.new_user_only and v.id not in granted:
            continue
        if v.ends_at and now >= v.ends_at:
            continue
        if v.id in used:
            status = USED
        elif v.new_user_only and user.created_at < now - timedelta(days=NEW_USER_WINDOW_DAYS):
            status = NOT_ELIGIBLE
        elif v.min_trust is not None and trust is not None and trust < v.min_trust:
            status = LOCKED
        else:
            status = USABLE
        items.append({"code": v.code, "description": v.description, "min_order_value": v.min_order_value,
                      "granted": v.id in granted, "status": status})
    # Mã shop tặng riêng lên đầu, rồi mã dùng được trước mã đang khóa / đã dùng
    items.sort(key=lambda i: (not i["granted"], i["status"] != USABLE))
    return items
