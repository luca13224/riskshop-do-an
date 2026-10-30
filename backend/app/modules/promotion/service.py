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
from app.modules.promotion.models import PERCENT, Voucher, VoucherRedemption

# Voucher tân thủ: chỉ cho tài khoản tạo trong vòng N ngày
NEW_USER_WINDOW_DAYS = 30


@dataclass(frozen=True)
class AppliedVoucher:
    id: int
    code: str
    description: str
    discount: int
    risk_checked: bool


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
