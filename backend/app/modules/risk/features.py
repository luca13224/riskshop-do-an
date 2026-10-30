"""Tính đặc trưng F01–F11 (docs/RULES_V0.md, mục 2).

Đây là lớp "feature store" của Risk Engine: ĐỌC (chỉ đọc) các bảng của module khác bằng SQL thuần,
không import code của cart/order, nên không tạo vòng phụ thuộc. Lý do: ADR-004.

Mọi đặc trưng chỉ dùng dữ liệu có TRƯỚC thời điểm đánh giá `as_of` (không nhìn tương lai).
Index tương ứng cho từng truy vấn: docs/ERD.md, mục 4.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

# Tham số làm mượt tỷ lệ COD thất bại: (thất bại + A) / (đã kết thúc + A + B), tỷ lệ nền A/(A+B) = 10%
SMOOTH_A, SMOOTH_B = 1, 9


@dataclass(frozen=True)
class FeatureInput:
    user_id: int
    user_created_at: datetime
    device_id: int | None
    ip_hash: str | None
    address_hash: str | None
    voucher_new_user: bool | None  # None: không có voucher
    payment_cod: bool | None  # None: chưa biết phương thức thanh toán
    order_value: int
    as_of: datetime


def _scalar(db: Session, sql: str, **params) -> int:
    return int(db.execute(text(sql), params).scalar() or 0)


def compute(db: Session, f: FeatureInput) -> dict:
    now = f.as_of
    age = now - f.user_created_at
    features: dict = {
        "account_age_hours": round(age.total_seconds() / 3600, 1),  # F01
        "signup_to_checkout_sec": int(age.total_seconds()),  # F06
        "voucher_new_user": f.voucher_new_user,
        "payment_cod": f.payment_cod,
        "order_value": f.order_value,  # F11
    }

    # F02: số tài khoản khách hàng MỚI (< 7 ngày) đã dùng cùng thiết bị trong 30 ngày, tính cả người hiện tại
    features["new_accounts_on_device_30d"] = (
        _scalar(
            db,
            """SELECT COUNT(DISTINCT ud.user_id) FROM user_devices ud JOIN users u ON u.id = ud.user_id
               WHERE ud.device_id = :d AND ud.last_seen_at >= :t30 AND u.created_at >= :t7 AND u.role = 'customer'""",
            d=f.device_id, t30=now - timedelta(days=30), t7=now - timedelta(days=7),
        )
        if f.device_id
        else None
    )

    # F03: số tài khoản dùng chung địa chỉ (đã chuẩn hóa) trong 30 ngày
    features["accounts_on_address_30d"] = (
        _scalar(
            db,
            "SELECT COUNT(DISTINCT user_id) FROM addresses WHERE norm_hash = :h AND created_at >= :t30",
            h=f.address_hash, t30=now - timedelta(days=30),
        )
        if f.address_hash
        else None
    )

    # F04: số tài khoản mới dùng cùng IP trong 24 giờ (tín hiệu yếu)
    features["new_accounts_on_ip_24h"] = (
        _scalar(
            db,
            """SELECT COUNT(DISTINCT ui.user_id) FROM user_ips ui JOIN users u ON u.id = ui.user_id
               WHERE ui.ip_hash = :h AND ui.last_seen_at >= :t24 AND u.created_at >= :t7 AND u.role = 'customer'""",
            h=f.ip_hash, t24=now - timedelta(hours=24), t7=now - timedelta(days=7),
        )
        if f.ip_hash
        else None
    )

    # F05: số lần thử voucher từ cùng thiết bị trong 10 phút
    features["voucher_attempts_device_10m"] = (
        _scalar(
            db,
            """SELECT COUNT(*) FROM events WHERE device_id = :d AND event_type = 'voucher_attempt'
               AND occurred_at >= :t AND occurred_at <= :now""",
            d=f.device_id, t=now - timedelta(minutes=10), now=now,
        )
        if f.device_id
        else None
    )

    # F06: số lượt xem sản phẩm trong 24 giờ (người thật thường xem trước khi mua)
    features["product_views_24h"] = _scalar(
        db,
        """SELECT COUNT(*) FROM events WHERE user_id = :u AND event_type = 'product_view'
           AND occurred_at >= :t AND occurred_at <= :now""",
        u=f.user_id, t=now - timedelta(hours=24), now=now,
    )

    # F07–F10: lịch sử đơn hàng (chỉ những đơn đã có kết quả trước as_of)
    row = db.execute(
        text(
            """SELECT
                 COALESCE(SUM(payment_method = 'COD' AND status IN ('DELIVERED','DELIVERY_FAILED')), 0) AS cod_finished,
                 COALESCE(SUM(payment_method = 'COD' AND status = 'DELIVERY_FAILED'), 0) AS cod_failed,
                 COALESCE(SUM(status = 'DELIVERED'), 0) AS delivered,
                 COALESCE(SUM(status = 'DELIVERY_FAILED'), 0) AS failed_all,
                 COALESCE(SUM(payment_method = 'COD' AND status IN ('PENDING_REVIEW','CONFIRMED','SHIPPING')), 0)
                   AS open_cod
               FROM orders WHERE user_id = :u AND created_at <= :now"""
        ),
        {"u": f.user_id, "now": now},
    ).one()
    cod_finished, cod_failed = int(row.cod_finished), int(row.cod_failed)
    delivered, failed_all = int(row.delivered), int(row.failed_all)
    features["cod_finished"] = cod_finished  # F07
    features["cod_failed"] = cod_failed
    features["cod_fail_rate_smoothed"] = round((cod_failed + SMOOTH_A) / (cod_finished + SMOOTH_A + SMOOTH_B), 4)  # F08
    features["delivered_orders"] = delivered  # F09
    finished_all = delivered + failed_all
    features["fail_rate_raw"] = round(failed_all / finished_all, 4) if finished_all else 0.0
    features["open_cod_orders"] = int(row.open_cod)  # F10
    return features
