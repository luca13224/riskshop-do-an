from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

FIXED = "fixed"  # giảm số tiền cố định
PERCENT = "percent"  # giảm theo %, có thể kèm mức giảm tối đa


class Voucher(Base):
    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)  # luôn lưu chữ in hoa
    description: Mapped[str] = mapped_column(String(255), default="")
    discount_type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[int] = mapped_column(BigInteger)  # VND nếu fixed, % nếu percent
    max_discount: Mapped[int | None] = mapped_column(BigInteger)  # trần giảm cho loại percent
    min_order_value: Mapped[int] = mapped_column(BigInteger, default=0)
    new_user_only: Mapped[bool] = mapped_column(Boolean, default=False)
    # True: khi áp voucher sẽ gọi Risk Engine (context voucher_apply). Nối ở module risk.
    risk_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    # Điểm tin cậy tối thiểu để dùng mã (Trust Score, bộ luật v3). Trust thấp hơn thì mã "tạm chưa áp dụng".
    # None = không xét. Mã giá trị cao đặt mức cao hơn, nên khi Trust giảm thì danh sách mã "co lại" dần.
    min_trust: Mapped[int | None] = mapped_column(Integer)
    max_redemptions: Mapped[int | None] = mapped_column(Integer)  # None = không giới hạn
    redeemed_count: Mapped[int] = mapped_column(Integer, default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserVoucher(Base):
    """Túi voucher: mã shop cấp riêng cho một tài khoản (ví dụ NGUOIMOI cấp khi tạo tài khoản).

    Mã công khai (không gắn tài khoản) không cần dòng ở đây; túi voucher hiển thị cả hai loại.
    """

    __tablename__ = "user_vouchers"
    __table_args__ = (UniqueConstraint("user_id", "voucher_id", name="uq_user_vouchers_user_voucher"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"))
    source: Mapped[str] = mapped_column(String(20), default="signup")  # vì sao được cấp
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class VoucherRedemption(Base):
    """Một lượt dùng voucher, ghi lúc đặt hàng.

    UNIQUE(voucher_id, user_id): mỗi tài khoản dùng mỗi voucher đúng 1 lần, kể cả khi
    hai request đặt hàng đến cùng lúc (CSDL là hàng rào cuối).
    """

    __tablename__ = "voucher_redemptions"
    __table_args__ = (UniqueConstraint("voucher_id", "user_id", name="uq_voucher_redemptions_voucher_user"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    voucher_id: Mapped[int] = mapped_column(ForeignKey("vouchers.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    discount_amount: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
