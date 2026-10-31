"""Tính đặc trưng F01–F16 (docs/RULES_V0.md, mục 2; F12–F13 thêm ở bộ luật v2, F14–F16 ở v3).

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
# F16: số đơn tối thiểu trong 90 ngày mới tính tỷ lệ trợ giá
SUBSIDY_MIN_ORDERS = 3


@dataclass(frozen=True)
class FeatureInput:
    user_id: int
    user_created_at: datetime
    device_id: int | None
    ip_hash: str | None
    address_hash: str | None
    address_phone: str | None  # SĐT nhận hàng của đơn này (chỉ có lúc đặt hàng)
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
        "device_id": f.device_id,  # không phải đặc trưng chấm điểm; lưu lại để gom case theo thiết bị
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

    # F12, F13 (v2): nhìn "cụm" quanh địa chỉ trên đồ thị liên kết: nút địa chỉ -> các tài khoản MỚI -> các IP
    # họ đã dùng. Farm phân tán: nhiều tài khoản mới cùng nhà nhưng mỗi người một mạng (đa dạng IP cao);
    # hộ gia đình thật thường chung Wi-Fi (đa dạng IP thấp). Xem docs/reviews/2026-10-31_RISK_V2_DESIGN.md.
    if f.address_hash:
        t7 = now - timedelta(days=7)
        cluster = db.execute(
            text(
                """SELECT COUNT(DISTINCT a.user_id) AS accounts, COUNT(DISTINCT ui.ip_hash) AS ips
                   FROM addresses a
                   JOIN users u ON u.id = a.user_id AND u.role = 'customer' AND u.created_at >= :t7
                   LEFT JOIN user_ips ui ON ui.user_id = a.user_id AND ui.last_seen_at >= :t7
                   WHERE a.norm_hash = :h AND a.created_at >= :t7"""
            ),
            {"h": f.address_hash, "t7": t7},
        ).one()
        accounts = int(cluster.accounts)
        features["new_accounts_on_address_7d"] = accounts  # F12
        features["address_ip_diversity_7d"] = round(int(cluster.ips) / accounts, 3) if accounts else None  # F13
    else:
        features["new_accounts_on_address_7d"] = None
        features["address_ip_diversity_7d"] = None

    # F14 (v3): một SĐT nhận hàng được bao nhiêu tài khoản dùng, ở bao nhiêu địa chỉ khác nhau, trong 30 ngày.
    # Cả nhà dùng chung SĐT của một người ở MỘT địa chỉ là bình thường (đã có R03 đếm); SĐT nhận hàng cho nhiều
    # tài khoản ở NHIỀU địa chỉ mới đáng ngờ (farm chia hàng về nhiều điểm nhận nhưng một người đi nhận).
    # SĐT đã được kiểm định dạng (10 chữ số) khi nhập nên so khớp trực tiếp. Index: addresses(phone, created_at).
    if f.address_phone:
        ph = db.execute(
            text(
                """SELECT COUNT(DISTINCT a.user_id) AS accounts, COUNT(DISTINCT a.norm_hash) AS addrs
                   FROM addresses a JOIN users u ON u.id = a.user_id
                   WHERE a.phone = :p AND a.created_at >= :t30 AND u.role = 'customer'"""
            ),
            {"p": f.address_phone, "t30": now - timedelta(days=30)},
        ).one()
        features["accounts_on_phone_30d"] = int(ph.accounts)
        features["addresses_on_phone_30d"] = int(ph.addrs)
    else:
        features["accounts_on_phone_30d"] = None
        features["addresses_on_phone_30d"] = None

    # F15 (v3): số địa chỉ khác nhau chính tài khoản này đã dùng trong 7 ngày (đổi địa chỉ liên tục)
    features["distinct_addresses_7d"] = _scalar(
        db, "SELECT COUNT(DISTINCT norm_hash) FROM addresses WHERE user_id = :u AND created_at >= :t7",
        u=f.user_id, t7=now - timedelta(days=7),
    )

    # F17 (ADR-011): liên kết với tài khoản ĐANG BỊ KHÓA VÔ THỜI HẠN (né lệnh khóa bằng tài khoản mới).
    # Đếm số LOẠI điểm chung trong 90 ngày: thiết bị, SĐT nhận hàng, địa chỉ. IP cố ý KHÔNG tính (Wi-Fi công cộng,
    # NAT nhà mạng). Chỉ tài khoản bị ban làm nguồn lây (không tính khóa tạm / khóa do liên kết) để tránh lây dây chuyền.
    t90 = now - timedelta(days=90)
    banned_sql = """SELECT user_id FROM account_restrictions WHERE kind = 'purchase_ban' AND lifted_at IS NULL"""
    links: dict[str, list[int]] = {}
    if f.device_id:
        links["thiết bị"] = [r[0] for r in db.execute(text(
            f"""SELECT DISTINCT user_id FROM user_devices WHERE device_id = :d AND user_id <> :u
                AND last_seen_at >= :t90 AND user_id IN ({banned_sql})"""), {"d": f.device_id, "u": f.user_id, "t90": t90})]
    if f.address_phone:
        links["SĐT nhận hàng"] = [r[0] for r in db.execute(text(
            f"""SELECT DISTINCT user_id FROM addresses WHERE phone = :p AND user_id <> :u
                AND created_at >= :t90 AND user_id IN ({banned_sql})"""), {"p": f.address_phone, "u": f.user_id, "t90": t90})]
    if f.address_hash:
        links["địa chỉ"] = [r[0] for r in db.execute(text(
            f"""SELECT DISTINCT user_id FROM addresses WHERE norm_hash = :h AND user_id <> :u
                AND created_at >= :t90 AND user_id IN ({banned_sql})"""), {"h": f.address_hash, "u": f.user_id, "t90": t90})]
    linked = {k: v for k, v in links.items() if v}
    features["banned_link_types_90d"] = len(linked)  # F17
    features["banned_links"] = {k: v[:3] for k, v in linked.items()}  # để giải thích: loại điểm chung -> tài khoản bị ban

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

    # F16 (v3): tỷ lệ "trợ giá" bằng voucher trong 90 ngày = tổng tiền giảm / tổng tiền hàng của các đơn hợp lệ.
    # Thay cho "lãi/lỗ" vì hệ thống không có giá vốn. Cần ít nhất SUBSIDY_MIN_ORDERS đơn, tránh khách mới
    # có 1 đơn dùng mã người mới bị tính tỷ lệ cao.
    sub = db.execute(
        text(
            """SELECT COUNT(*) AS n, COALESCE(SUM(discount), 0) AS disc, COALESCE(SUM(subtotal), 0) AS gross
               FROM orders WHERE user_id = :u AND created_at >= :t90 AND created_at <= :now
               AND status NOT IN ('REJECTED', 'CANCELLED')"""
        ),
        {"u": f.user_id, "t90": now - timedelta(days=90), "now": now},
    ).one()
    features["orders_90d"] = int(sub.n)
    features["voucher_subsidy_ratio_90d"] = (
        round(int(sub.disc) / int(sub.gross), 4) if int(sub.n) >= SUBSIDY_MIN_ORDERS and int(sub.gross) else None
    )
    return features
