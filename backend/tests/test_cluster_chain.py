"""Test R18 / F18 (ADR-016): cụm tài khoản mới nối chuỗi qua nhiều loại điểm chung cùng gom mã người mới."""

from tests.test_linked_ban import order, try_voucher
from tests.test_risk_scenarios import ADDRESS, browse, customer, hit_codes, last_decision, shop  # noqa: F401


def addr(n: int, phone: str) -> dict:
    return {**ADDRESS, "line": f"{n} Ngõ Chuỗi {n}", "phone": phone}


def member(email: str, device: str, address: dict | None, ip: str):
    """Tài khoản mới: xem hàng, áp mã người mới, đặt hàng trả trước (lưu địa chỉ / SĐT nhận hàng)."""
    c = customer(email, device, ip=ip)
    browse(c)
    r = try_voucher(c)
    if address is not None and r.status_code == 200:
        order(c, address)  # có thể bị luật địa chỉ cũ (R03, R11) gỡ mã: không phải việc của test này
    return r


def test_chain_of_five_new_accounts_loses_welcome_code(shop, db):
    # A -thiết bị- B -SĐT- C -địa chỉ- D -thiết bị- E: không cặp nào chung quá một thứ
    assert member("a@ex.com", "dev-chuoi-0001", addr(1, "0911000001"), "198.51.100.1").status_code == 200
    assert member("b@ex.com", "dev-chuoi-0001", addr(2, "0911000002"), "198.51.100.2").status_code == 200
    assert member("c@ex.com", "dev-chuoi-0003", addr(3, "0911000002"), "198.51.100.3").status_code == 200
    assert member("d@ex.com", "dev-chuoi-0004", addr(3, "0911000004"), "198.51.100.4").status_code == 200
    r = member("e@ex.com", "dev-chuoi-0004", None, "198.51.100.5")
    assert r.status_code == 409
    d = last_decision(db, "e@ex.com")
    snap = d.features_snapshot
    assert snap["cluster_new_accounts_30d"] == 5 and snap["cluster_voucher_accounts_30d"] == 5
    assert snap["cluster_link_types"] == 2 and snap["cluster_links"] == ["address", "device", "phone"]
    assert "CLUSTER_CHAIN" in hit_codes(db, d)


def test_family_of_four_on_one_device_keeps_code(shop, db):
    home = addr(9, "0922000000")
    for i in range(4):
        member(f"nha{i}@ex.com", "dev-nha-chung-01", {**home, "phone": f"092200000{i + 1}"}, f"198.51.100.{20 + i}")
    d = last_decision(db, "nha3@ex.com")
    assert d.features_snapshot["cluster_link_types"] == 2  # chung máy + chung địa chỉ, nhưng mới 4 tài khoản
    assert "CLUSTER_CHAIN" not in hit_codes(db, d)


def test_cluster_with_only_one_link_type_is_left_to_count_rules(shop, db):
    # 5 tài khoản mới, mỗi người một máy, một SĐT, cùng giao về một địa chỉ: R03 / R11 xử lý, không phải R18
    home = addr(7, "0933000000")
    for i in range(5):
        member(f"tro{i}@ex.com", f"dev-tro-{i:04d}", {**home, "phone": f"093300000{i + 1}"}, f"198.51.100.{40 + i}")
    c = customer("tro5@ex.com", "dev-tro-0099", ip="198.51.100.49")
    browse(c)
    try_voucher(c)
    assert order(c, {**home, "phone": "0933000099"}).status_code in (201, 403, 409)
    d = last_decision(db, "tro5@ex.com")
    assert d.features_snapshot["cluster_link_types"] == 1
    assert "CLUSTER_CHAIN" not in hit_codes(db, d)


def test_cluster_not_computed_without_welcome_code(shop, db):
    c = customer("thuong@ex.com", "dev-thuong-0001")
    browse(c)
    c.post("/api/cart/items", json={"product_id": 1, "quantity": 1})
    assert order(c, addr(5, "0944000000")).status_code == 201
    assert last_decision(db, "thuong@ex.com").features_snapshot["cluster_new_accounts_30d"] is None
