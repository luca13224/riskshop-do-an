"""Test danh sách tài khoản bị hạn chế quyền mua hàng (Console): trạng thái, lọc, che email, phân quyền."""

from datetime import timedelta

from sqlalchemy import select

from app.core.time import utcnow
from app.modules.auth.models import ANALYST, RISK_MANAGER, User
from app.modules.risk.models import PURCHASE_BAN, PURCHASE_COOLDOWN, PURCHASE_LINKED, AccountRestriction
from tests.test_risk_scenarios import customer, shop  # noqa: F401 (fixture shop)
from tests.test_rules_admin import login

URL = "/api/console/risk/restrictions"


def uid(db, email: str) -> int:
    return db.scalar(select(User.id).where(User.email == email))


def seed(db):
    """4 tài khoản: khóa vô thời hạn, khóa 24 giờ còn hạn, khóa liên kết đã hết hạn, khóa 24 giờ đã gỡ."""
    for email in ("ban@ex.com", "cool@ex.com", "old@ex.com", "freed@ex.com"):
        customer(email, f"dev-{email.split('@')[0]}-0001")
    now = utcnow()
    db.add_all([
        AccountRestriction(user_id=uid(db, "ban@ex.com"), kind=PURCHASE_BAN, reason="Nhân viên khóa", source="staff"),
        AccountRestriction(user_id=uid(db, "cool@ex.com"), kind=PURCHASE_COOLDOWN, reason="4 lần bị từ chối",
                           expires_at=now + timedelta(hours=20)),
        AccountRestriction(user_id=uid(db, "old@ex.com"), kind=PURCHASE_LINKED, reason="Liên kết thiết bị",
                           created_at=now - timedelta(days=40), expires_at=now - timedelta(days=10)),
        AccountRestriction(user_id=uid(db, "freed@ex.com"), kind=PURCHASE_COOLDOWN, reason="4 lần bị từ chối",
                           expires_at=now + timedelta(hours=10), lifted_at=now, lift_reason="Đã xác minh khách thật"),
    ])
    db.commit()


def test_default_lists_only_active_with_counts_and_masked_email(shop, db):
    seed(db)
    analyst = login(db, "an@riskshop.test", ANALYST)  # nhân viên nào cũng xem được
    body = analyst.get(URL).json()
    assert body["status_counts"] == {"active": 2, "expired": 1, "lifted": 1}
    assert body["total"] == 2 and {r["kind"] for r in body["items"]} == {PURCHASE_BAN, PURCHASE_COOLDOWN}
    assert all("***@" in r["user_email"] for r in body["items"])
    ban = next(r for r in body["items"] if r["kind"] == PURCHASE_BAN)
    assert ban["source"] == "staff" and ban["expires_at"] is None and ban["status"] == "active"


def test_filters_by_status_kind_and_search(shop, db):
    seed(db)
    analyst = login(db, "an@riskshop.test", ANALYST)
    assert [r["status"] for r in analyst.get(URL, params={"status": "expired"}).json()["items"]] == ["expired"]
    lifted = analyst.get(URL, params={"status": "lifted"}).json()["items"]
    assert len(lifted) == 1 and lifted[0]["lift_reason"] == "Đã xác minh khách thật"
    assert analyst.get(URL, params={"status": "all"}).json()["total"] == 4
    assert analyst.get(URL, params={"status": "all", "kind": PURCHASE_COOLDOWN}).json()["total"] == 2
    assert analyst.get(URL, params={"status": "all", "q": "cool@"}).json()["total"] == 1
    assert analyst.get(URL, params={"status": "bad"}).status_code == 422


def test_lift_from_list_shows_who_lifted(shop, db):
    seed(db)
    manager = login(db, "rm@riskshop.test", RISK_MANAGER)
    target = uid(db, "ban@ex.com")
    r = manager.post(f"/api/console/risk/users/{target}/restriction/lift", json={"reason": "Khiếu nại hợp lệ, gỡ khóa"})
    assert r.status_code == 200
    row = next(x for x in manager.get(URL, params={"status": "lifted"}).json()["items"] if x["user_id"] == target)
    assert row["lifted_by_name"] == "rm" and row["lift_reason"] == "Khiếu nại hợp lệ, gỡ khóa"
    assert manager.get(URL).json()["status_counts"]["active"] == 1


def test_customer_cannot_list(shop, db):
    c = customer("khach@ex.com", "dev-khach-0001")
    assert c.get(URL).status_code == 403
