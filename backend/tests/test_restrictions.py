"""Test khóa quyền mua hàng tự động khi cố đặt hàng lặp lại sau nhiều lần bị từ chối (ADR-010)."""

from datetime import timedelta

from sqlalchemy import select

from app.core.jobs import Job
from app.core.time import utcnow
from app.modules.audit.models import AuditLog
from app.modules.auth.models import ANALYST, RISK_MANAGER
from app.modules.order.models import COD, PREPAID
from app.modules.risk.models import PURCHASE_BAN, PURCHASE_COOLDOWN, AccountRestriction, RiskDecision
from tests.test_privacy import staff
from tests.test_risk_scenarios import add_history, browse, checkout, customer, last_decision, shop  # noqa: F401

MESSAGE = "Tôi bấm đặt hàng nhiều lần vì tưởng mạng lỗi, mong được mở lại tài khoản."


def bad_cod_customer(db, email="khang@example.com"):
    """Khách có lịch sử bùng hàng COD (1 giao / 4 thất bại) -> đặt COD bị từ chối (409), đơn không được tạo."""
    c = customer(email, f"device-{email[:5]}-0001")
    add_history(db, email, cod_delivered=1, cod_failed=4)
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    return c


def restrictions(db):
    db.rollback()
    return list(db.scalars(select(AccountRestriction).order_by(AccountRestriction.id)))


def test_fourth_refusal_triggers_24h_cooldown_and_block(shop, db):
    c = bad_cod_customer(db)
    for _ in range(3):  # 3 lần bị từ chối: chưa khóa
        assert checkout(c, COD).json()["error"]["code"] == "COD_NOT_AVAILABLE"
    assert restrictions(db) == []

    r = checkout(c, COD)  # lần thứ 4 -> khóa 24 giờ, quyết định CHẶN
    assert r.status_code == 403 and r.json()["error"]["code"] == "ORDER_BLOCKED"
    assert "khiếu nại" in r.json()["error"]["message"] and "COD" not in r.json()["error"]["message"]
    (res,) = restrictions(db)
    assert res.kind == PURCHASE_COOLDOWN and res.source == "auto"
    assert timedelta(hours=23) < res.expires_at - res.created_at <= timedelta(hours=24)
    d = last_decision(db, "khang@example.com")
    assert d.decision == "BLOCK" and d.actions["restrict_account"] and d.actions["open_case"]
    assert db.scalar(select(Job.id).where(Job.job_type == "open_case"))  # case tự mở
    assert db.scalar(select(AuditLog.action).where(AuditLog.action == "account.restrict"))

    # Đang khóa: trả trước cũng bị chặn, và các lần này không cộng dồn thành khóa mới
    for method in (PREPAID, COD, PREPAID):
        assert checkout(c, method).status_code == 403
    assert len(restrictions(db)) == 1


def test_repeat_within_30_days_becomes_permanent_ban(shop, db):
    c = bad_cod_customer(db)
    for _ in range(4):
        checkout(c, COD)
    (first,) = restrictions(db)
    # Giả lập đã qua 25 giờ: lùi thời gian của lệnh khóa VÀ các lần bị từ chối trước đó
    first.created_at -= timedelta(hours=25)
    first.expires_at = utcnow() - timedelta(hours=1)
    for d in db.scalars(select(RiskDecision).where(RiskDecision.user_id == first.user_id)):
        d.created_at -= timedelta(hours=25)
    db.commit()

    assert checkout(c, PREPAID).status_code == 201  # hết khóa: mua trả trước lại được
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    for _ in range(3):
        assert checkout(c, COD).status_code == 409  # bộ đếm tính lại từ lần khóa trước
    assert checkout(c, COD).status_code == 403  # tái phạm trong 30 ngày
    latest = restrictions(db)[-1]
    assert latest.kind == PURCHASE_BAN and latest.expires_at is None


def test_only_risk_manager_can_lift_with_reason(shop, db):
    c = bad_cod_customer(db)
    for _ in range(4):
        checkout(c, COD)
    user_id = last_decision(db, "khang@example.com").user_id

    analyst = staff(db, "an@riskshop.test", ANALYST)
    assert analyst.get(f"/api/console/risk/users/{user_id}/restriction").json()["kind"] == PURCHASE_COOLDOWN
    body = {"reason": "Đã gọi điện xác minh, khách bấm lặp do mạng chậm."}
    assert analyst.post(f"/api/console/risk/users/{user_id}/restriction/lift", json=body).status_code == 403

    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)
    assert manager.post(f"/api/console/risk/users/{user_id}/restriction/lift",
                        json={"reason": "ngắn"}).status_code == 422  # bắt buộc lý do đủ dài
    assert manager.post(f"/api/console/risk/users/{user_id}/restriction/lift", json=body).status_code == 200
    assert manager.get(f"/api/console/risk/users/{user_id}/restriction").json() is None
    assert manager.post(f"/api/console/risk/users/{user_id}/restriction/lift", json=body).status_code == 409
    db.rollback()
    assert db.scalar(select(AuditLog.note).where(AuditLog.action == "account.unrestrict")) == body["reason"]
    assert checkout(c, PREPAID).status_code == 201


def test_accepted_appeal_lifts_restriction(shop, db):
    c = bad_cod_customer(db)
    for _ in range(4):
        checkout(c, COD)
    item = next(i for i in c.get("/api/appeals/eligible").json() if i["label"].startswith("Tài khoản"))
    code = c.post("/api/appeals", json={"decision_id": item["decision_id"], "policy": item["policy"],
                                        "message": MESSAGE}).json()["appeal_code"]
    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)
    resolve = {"outcome": "ACCEPTED", "response": "Đã xem lại, mở khóa tài khoản cho bạn."}
    assert manager.post(f"/api/console/appeals/{code}/resolve", json=resolve).status_code == 200
    assert all(r.lifted_at is not None for r in restrictions(db))
    assert checkout(c, PREPAID).status_code == 201
