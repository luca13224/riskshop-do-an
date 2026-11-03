"""Test né lệnh khóa bằng tài khoản mới (ADR-011).

Khóa thanh toán khi chung >= 2 loại điểm mạnh (thiết bị, SĐT nhận hàng, địa chỉ) với tài khoản đang bị ban,
hoặc chung 1 loại VÀ spam mã người mới. Chung 1 loại mà không spam (người nhà dùng chung máy): chỉ trừ điểm tin cậy
và mở case. Chung IP: không tính.
"""

import uuid
from datetime import timedelta

from sqlalchemy import select

from app.core.jobs import Job
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.order.models import PREPAID
from app.modules.risk.models import PURCHASE_BAN, PURCHASE_LINKED, AccountRestriction
from tests.test_risk_scenarios import ADDRESS, browse, customer, hit_codes, last_decision, shop  # noqa: F401

HOME = {**ADDRESS, "line": "15 Ngõ Nhà Bố", "phone": "0911000111"}


def order(c, address, method=PREPAID):
    return c.post("/api/orders/checkout", json={"address": address, "payment_method": method},
                  headers={"Idempotency-Key": str(uuid.uuid4())})


def banned_dad(db, device="device-nha-0001", ip="203.0.113.50"):
    """Bố: đặt một đơn về nhà (có địa chỉ, SĐT), rồi bị khóa vô thời hạn."""
    c = customer("bo@example.com", device, ip=ip)
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert order(c, HOME).status_code == 201
    db.rollback()
    uid = db.scalar(select(User.id).where(User.email == "bo@example.com"))
    db.add(AccountRestriction(user_id=uid, kind=PURCHASE_BAN, reason="test", source="staff"))
    db.commit()
    return uid


def linked_locks(db, email):
    db.rollback()
    uid = db.scalar(select(User.id).where(User.email == email))
    return list(db.scalars(select(AccountRestriction).where(AccountRestriction.user_id == uid,
                                                            AccountRestriction.kind == PURCHASE_LINKED)))


def try_voucher(c):
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    return c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})


def test_family_member_on_shared_device_is_not_locked(shop, db):
    banned_dad(db)
    con = customer("con@example.com", "device-nha-0001", ip="198.51.100.20")  # dùng chung máy của bố
    browse(con)
    r = try_voucher(con)  # thử mã MỘT lần: chưa phải spam
    # ADR-013: chung 1 điểm chỉ trừ điểm tin cậy (R16 không cộng vào điểm voucher), nên vẫn dùng được mã người mới
    assert r.status_code == 200
    d = last_decision(db, "con@example.com")
    assert d.features_snapshot["banned_link_types_90d"] == 1
    assert "LINKED_TO_BANNED" not in hit_codes(db, d)
    assert d.features_snapshot["trust_deductions"]["LINKED_TO_BANNED"] == 35
    assert 50 <= d.features_snapshot["trust_score"] < 70  # bậc "theo dõi": đủ cho NGUOIMOI, không đủ cho GIAM10
    assert db.scalar(select(Job.id).where(Job.job_type == "open_case"))  # analyst được báo để xem
    assert linked_locks(db, "con@example.com") == []  # KHÔNG khóa thanh toán
    # Con mua được bằng địa chỉ của mình
    assert order(con, {**ADDRESS, "line": "2 Phố Con", "phone": "0922000222"}).status_code == 201
    assert linked_locks(db, "con@example.com") == []


def test_evader_who_keeps_the_code_is_locked_at_checkout(shop, db):
    """ADR-013: kẻ né khóa không bị gỡ mã ở bước áp mã (mới thấy 1 điểm), nên đi tiếp; tới bước đặt hàng
    hệ thống thấy thêm địa chỉ / SĐT của tài khoản bị khóa (>= 2 điểm) thì chặn đơn và khóa thanh toán."""
    dad = banned_dad(db)
    alt = customer("ne-khoa@example.com", "device-nha-0001", ip="198.51.100.22")
    assert try_voucher(alt).status_code == 200
    blocked = order(alt, HOME)  # giao về đúng địa chỉ / SĐT của tài khoản bị khóa
    assert blocked.status_code == 403
    (lock,) = linked_locks(db, "ne-khoa@example.com")
    assert f"#{dad}" in lock.reason


def test_new_account_spamming_welcome_code_gets_30_day_lock(shop, db):
    dad = banned_dad(db)
    alt = customer("acc-moi@example.com", "device-nha-0001", ip="198.51.100.21")
    try_voucher(alt)
    r = alt.post("/api/cart/voucher", json={"code": "NGUOIMOI"})  # lần thử thứ 2 trên cùng máy: spam
    assert r.status_code == 409 and "khiếu nại" in r.json()["error"]["message"]
    (lock,) = linked_locks(db, "acc-moi@example.com")
    assert timedelta(days=29) < lock.expires_at - lock.created_at <= timedelta(days=30)
    assert f"#{dad}" in lock.reason and "thiết bị" in lock.reason
    # Đang khóa: đặt hàng bị chặn
    blocked = order(alt, {**ADDRESS, "line": "9 Đường Khác", "phone": "0933000333"})
    assert blocked.status_code == 403 and blocked.json()["error"]["code"] == "ORDER_BLOCKED"


def test_two_strong_links_lock_even_without_voucher(shop, db):
    banned_dad(db)
    # Máy khác, IP khác, nhưng giao về đúng nhà và đúng SĐT của tài khoản bị khóa
    alt = customer("acc-khac@example.com", "device-khac-0002", ip="198.51.100.22")
    browse(alt)
    alt.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    r = order(alt, HOME)
    assert r.status_code == 403
    d = last_decision(db, "acc-khac@example.com")
    assert d.decision == "BLOCK" and d.features_snapshot["banned_link_types_90d"] == 2
    (lock,) = linked_locks(db, "acc-khac@example.com")
    assert "SĐT nhận hàng" in lock.reason and "địa chỉ" in lock.reason


def test_repeat_linked_lock_is_60_days(shop, db):
    banned_dad(db)
    alt = customer("taiphan@example.com", "device-khac-0003", ip="198.51.100.23")
    alt.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    order(alt, HOME)
    (first,) = linked_locks(db, "taiphan@example.com")
    first.expires_at = utcnow() - timedelta(minutes=1)  # đã hết hạn khóa 30 ngày
    db.commit()
    order(alt, HOME)
    locks = linked_locks(db, "taiphan@example.com")
    assert len(locks) == 2 and timedelta(days=59) < locks[-1].expires_at - locks[-1].created_at
    assert "tái phạm" in locks[-1].reason


def test_shared_ip_alone_never_counts(shop, db):
    banned_dad(db, ip="203.0.113.77")
    cafe = customer("quan-cafe@example.com", "device-cafe-0004", ip="203.0.113.77")  # chỉ chung Wi-Fi
    try_voucher(cafe)
    cafe.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    d = last_decision(db, "quan-cafe@example.com")
    assert d.features_snapshot["banned_link_types_90d"] == 0
    assert linked_locks(db, "quan-cafe@example.com") == []


def test_lifted_ban_no_longer_spreads(shop, db):
    dad = banned_dad(db)
    db.scalar(select(AccountRestriction).where(AccountRestriction.user_id == dad)).lifted_at = utcnow()
    db.commit()
    alt = customer("sau-go@example.com", "device-nha-0001", ip="198.51.100.24")
    try_voucher(alt)
    alt.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    assert last_decision(db, "sau-go@example.com").features_snapshot["banned_link_types_90d"] == 0
    assert linked_locks(db, "sau-go@example.com") == []


def test_banned_account_is_marked_in_link_graph(shop, db):
    from tests.test_privacy import staff
    from app.modules.auth.models import ANALYST

    dad = banned_dad(db)
    con = customer("con2@example.com", "device-nha-0001", ip="198.51.100.25")
    try_voucher(con)
    analyst = staff(db, "an@riskshop.test", ANALYST)
    g = analyst.get(f"/api/console/risk/graph/{dad}").json()
    marks = {n["user_id"]: n["banned"] for n in g["nodes"] if n["type"] == "account"}
    assert marks[dad] is True and g["summary"]["banned"] == 1
