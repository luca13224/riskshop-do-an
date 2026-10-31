"""Đồ thị liên kết tài khoản: farm cùng thiết bị gom thành một cụm, khách độc lập không bị dính vào, PII được che."""

from app.modules.auth.models import ANALYST, User
from tests.test_privacy import staff
from tests.test_risk_scenarios import browse, checkout, customer, shop  # noqa: F401


def user_id(db, email):
    db.rollback()
    return db.query(User).filter_by(email=email).one().id


def test_farm_on_one_device_forms_one_cluster(shop, db):
    for i in range(1, 5):
        c = customer(f"farm{i}@example.com", "device-farm-0001")
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        c.post("/api/cart/voucher", json={"code": "NGUOIMOI"})
    customer("doclap@example.com", "device-solo-0001", ip="198.51.100.99")  # khách không liên quan

    analyst = staff(db, "an@riskshop.test", ANALYST)
    g = analyst.get(f"/api/console/risk/graph/{user_id(db, 'farm1@example.com')}").json()
    accounts = [n for n in g["nodes"] if n["type"] == "account"]
    assert len(accounts) == 4 and g["summary"]["accounts"] == 4
    assert g["summary"]["new_accounts"] == 4 and g["summary"]["restricted_accounts"] >= 1
    device = [n for n in g["nodes"] if n["type"] == "device"]
    assert len(device) == 1 and device[0]["accounts"] == 4  # một thiết bị nối cả 4 tài khoản
    assert sum(1 for e in g["edges"] if e["target"] == device[0]["id"]) == 4
    assert [n for n in accounts if n["root"]][0]["label"] == "fa***@example.com"  # email đã che
    assert "doclap" not in str(g) and "example.com\"" not in str(g)


def test_shared_address_links_accounts_and_hides_street(shop, db):
    # Hai tài khoản khác thiết bị, khác IP nhưng giao về cùng một địa chỉ
    for i, dev in enumerate(["device-a-000001", "device-b-000001"], start=1):
        c = customer(f"giao{i}@example.com", dev, ip=f"192.0.2.{i}")
        browse(c)
        c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
        assert checkout(c).status_code == 201
    g = staff(db, "an@riskshop.test", ANALYST).get(f"/api/console/risk/graph/{user_id(db, 'giao1@example.com')}").json()
    addr = [n for n in g["nodes"] if n["type"] == "address"]
    assert len(addr) == 1 and addr[0]["accounts"] == 2
    assert g["summary"]["accounts"] == 2
    assert all(ch.isalpha() or ch in " ,.-" for ch in addr[0]["label"].replace("đ", "d"))  # chỉ phường, quận, không số nhà


def test_graph_permissions(shop, db, client):
    c = customer("minh@example.com", "device-minh-0001")
    uid = user_id(db, "minh@example.com")
    assert c.get(f"/api/console/risk/graph/{uid}").status_code == 403  # khách không xem được
    analyst = staff(db, "an@riskshop.test", ANALYST)
    assert analyst.get("/api/console/risk/graph/999999").status_code == 404
    g = analyst.get(f"/api/console/risk/graph/{uid}").json()
    assert g["summary"]["accounts"] == 1  # khách độc lập: chỉ có chính mình
