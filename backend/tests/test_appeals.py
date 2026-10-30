"""Test khiếu nại (ADR-006): khách gửi khiếu nại cho quyết định hạn chế, quản lý xét lại,
chấp nhận thì miễn trừ chính sách và duyệt đơn đang giữ."""

from sqlalchemy import select

from app.modules.audit.models import AuditLog
from app.modules.auth.models import ANALYST, RISK_MANAGER
from app.modules.order.models import Order
from app.modules.risk.models import RiskAllowlist
from tests.test_privacy import staff
from tests.test_risk_scenarios import browse, checkout, customer, hit_codes, last_decision, shop  # noqa: F401

MESSAGE = "Tôi là khách thật, mua màn hình cho công việc, mong được xác nhận đơn."


def held_order(email="minh.nguyen@example.com"):
    """Tài khoản mới đặt COD 5,49 triệu -> đơn bị giữ chờ duyệt (cảnh 5b)."""
    c = customer(email, f"device-{email[:4]}-0001")
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    assert checkout(c).status_code == 201
    return c


def test_customer_sees_eligible_without_rule_details(shop, db):
    c = held_order()
    items = c.get("/api/appeals/eligible").json()
    assert len(items) == 1
    item = items[0]
    assert item["policy"] == "cod" and item["label"] == "Đơn hàng bị giữ lại chờ xác minh"
    assert item["order_status"] == "PENDING_REVIEW" and item["open_appeal"] is None
    assert "rule" not in str(item).lower() and "score" not in item  # không lộ luật hay điểm


def test_create_appeal_once_and_validate(shop, db):
    c = held_order()
    decision_id = c.get("/api/appeals/eligible").json()[0]["decision_id"]
    body = {"decision_id": decision_id, "policy": "cod", "message": MESSAGE}

    assert c.post("/api/appeals", json={**body, "message": "ngắn quá"}).status_code == 422
    assert c.post("/api/appeals", json={**body, "policy": "voucher"}).json()["error"]["code"] == "NOT_RESTRICTED"
    r = c.post("/api/appeals", json=body)
    assert r.status_code == 201 and r.json()["status"] == "OPEN"
    assert c.post("/api/appeals", json=body).json()["error"]["code"] == "ALREADY_APPEALED"
    # Đã khiếu nại thì không còn trong danh sách có thể khiếu nại
    assert c.get("/api/appeals/eligible").json() == []

    other = customer("khac@example.com", "device-khac-0001")
    assert other.post("/api/appeals", json=body).status_code == 404  # không khiếu nại hộ người khác được


def test_manager_accepts_appeal_approves_order_and_exempts(shop, db):
    c = held_order()
    decision_id = c.get("/api/appeals/eligible").json()[0]["decision_id"]
    code = c.post("/api/appeals", json={"decision_id": decision_id, "policy": "cod", "message": MESSAGE}).json()[
        "appeal_code"
    ]

    analyst = staff(db, "an@riskshop.test", ANALYST)
    listed = analyst.get("/api/console/appeals").json()
    assert listed[0]["appeal_code"] == code and listed[0]["user_email"] == "mi***@example.com"
    detail = analyst.get(f"/api/console/appeals/{code}").json()
    assert detail["decision"]["decision"] == "REVIEW" and detail["decision"]["hits"]
    resolve = {"outcome": "ACCEPTED", "response": "Đã xác minh qua điện thoại, đơn của bạn được duyệt."}
    assert analyst.post(f"/api/console/appeals/{code}/resolve", json=resolve).status_code == 403

    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)
    r = manager.post(f"/api/console/appeals/{code}/resolve", json=resolve)
    assert r.status_code == 200 and r.json()["status"] == "ACCEPTED"
    assert r.json()["active_exemptions"] == ["cod"]
    assert manager.post(f"/api/console/appeals/{code}/resolve", json=resolve).status_code == 409

    db.rollback()
    assert db.scalar(select(Order.status)) == "CONFIRMED"
    assert db.scalar(select(RiskAllowlist.policy)) == "cod"
    log = db.scalar(select(AuditLog).where(AuditLog.action == "appeal.resolve"))
    assert log.entity_id == code and log.after_data["order_status"] == "CONFIRMED"
    mine = c.get("/api/appeals").json()[0]
    assert mine["status"] == "ACCEPTED" and mine["response"].startswith("Đã xác minh")

    # Lần sau khách đặt COD giá trị cao: luật vẫn khớp và được ghi lại, nhưng không bị giữ đơn nữa
    browse(c, "man-hinh")
    c.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    assert checkout(c).json()["status"] == "CONFIRMED"
    d = last_decision(db, "minh.nguyen@example.com")
    assert d.decision == "ALLOW" and d.features_snapshot["exempt_policies"] == ["cod"]
    assert hit_codes(db, d)  # luật vẫn được ghi, không bị "tắt"


def test_voucher_exemption_after_accepted_appeal(shop, db):
    # Tài khoản thứ 3 trên cùng thiết bị bị gỡ voucher (farm), nhưng thực ra là người nhà dùng chung máy
    for i in range(1, 4):
        c = customer(f"nha{i}@example.com", "device-chung-0001")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        last = c.post("/api/cart/voucher", json={"code": "TANTHU"})
    assert last.status_code == 409
    item = c.get("/api/appeals/eligible").json()[0]
    assert item["policy"] == "voucher" and item["label"] == "Mã giảm giá không được áp dụng"
    code = c.post("/api/appeals", json={"decision_id": item["decision_id"], "policy": "voucher",
                                        "message": "Máy tính dùng chung trong gia đình, tôi là khách mới thật."}
                  ).json()["appeal_code"]
    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)
    manager.post(f"/api/console/appeals/{code}/resolve",
                 json={"outcome": "ACCEPTED", "response": "Đã xác minh, bạn dùng được mã tân thủ."})
    assert c.post("/api/cart/voucher", json={"code": "TANTHU"}).status_code == 200


def test_rejected_appeal_gives_no_exemption_and_frees_slot(shop, db):
    c = held_order()
    decision_id = c.get("/api/appeals/eligible").json()[0]["decision_id"]
    code = c.post("/api/appeals", json={"decision_id": decision_id, "policy": "cod", "message": MESSAGE}).json()[
        "appeal_code"
    ]
    manager = staff(db, "manager@riskshop.test", RISK_MANAGER)
    r = manager.post(f"/api/console/appeals/{code}/resolve",
                     json={"outcome": "REJECTED", "response": "Chưa xác minh được thông tin, vui lòng chọn trả trước."})
    assert r.json()["status"] == "REJECTED" and r.json()["active_exemptions"] == []
    db.rollback()
    assert db.scalar(select(Order.status)) == "PENDING_REVIEW"  # từ chối khiếu nại không tự đổi đơn
    assert db.scalar(select(RiskAllowlist.id)) is None
    assert manager.get("/api/console/dashboard").json()["attention"]["open_appeals"] == 0


def test_appeal_api_permissions(shop, db, client):
    assert client.get("/api/appeals").status_code == 401
    analyst = staff(db, "an@riskshop.test", ANALYST)
    assert analyst.get("/api/appeals").status_code == 403  # nhân viên không có khiếu nại của khách
    assert analyst.get("/api/console/appeals/KHONGCO").status_code == 404
