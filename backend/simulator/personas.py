"""Persona của bộ mô phỏng: người dùng hợp lệ, hard negative (hợp lệ nhưng dễ bị nhầm), kẻ lạm dụng,
và biến thể lạm dụng CHƯA BIẾT (chỉ có ở tập test, luật không được thiết kế riêng cho chúng).

Tham số của tập test RỘNG HƠN tập dev, để đo khả năng tổng quát hóa thay vì "học thuộc" tập dev.
Mọi tỷ lệ, khoảng giá trị ở đây là GIẢ ĐỊNH mô phỏng, không phải số liệu thật của sàn nào.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

# Bậc giá (SKU trong seed sản phẩm)
CHEAP = ["SM-002", "PH-001", "CP-002", "AU-002", "GR-001", "AU-001"]  # 149k–590k
MID = ["GR-002", "CP-001", "AU-003", "SP-003"]  # 890k–2,39 triệu
# Đơn giá trị cao: (sku, số lượng)
HIGH = [("CP-003", 1), ("AU-003", 2), ("SP-003", 2)]  # 5,49 tr / 3,78 tr / 4,78 tr

DATASETS: dict[str, dict] = {
    "dev": {
        "normal_new": {"n": 100, "voucher_prob": 0.5, "cod_prob": 0.5},
        "loyal": {"n": 30, "delivered": (5, 40), "fail_rate": (0.0, 0.1), "high_value_prob": 0.3},
        "family": {"n": 8, "size": (2, 4)},
        "new_high_value": {"n": 8},
        "repeat_buyer": {"n": 8, "orders": 3},
        "farm": {"n": 6, "accounts": (4, 7), "devices": (1, 2), "rotate_ip_prob": 0.0, "address_variants": False},
        "cod_bomber": {"n": 12, "finished": (3, 10), "fail_rate": (0.5, 0.9)},
    },
    "test": {
        "normal_new": {"n": 150, "voucher_prob": 0.6, "cod_prob": 0.5},
        "loyal": {"n": 40, "delivered": (3, 60), "fail_rate": (0.0, 0.15), "high_value_prob": 0.35},
        "family": {"n": 10, "size": (2, 6)},
        "new_high_value": {"n": 10},
        "repeat_buyer": {"n": 10, "orders": 4},
        "farm": {"n": 8, "accounts": (3, 10), "devices": (1, 4), "rotate_ip_prob": 0.5, "address_variants": True},
        "cod_bomber": {"n": 15, "finished": (3, 12), "fail_rate": (0.35, 0.95)},
        # Biến thể chưa biết
        "farm_spread": {"n": 4, "accounts": (5, 8)},  # mỗi tài khoản một thiết bị, đổi IP, địa chỉ viết khác nhau
        "cod_hoarder": {"n": 6, "orders": (3, 4)},  # tài khoản mới đặt dồn nhiều đơn COD rồi bỏ
    },
}

FARM_ADDRESS_VARIANTS = [
    "Số 5 Ngõ 12 Láng Hạ", "so 05 ngo 12 lang ha", "5, Ngõ 12, Láng Hạ", "Số 05 - Ngõ 12 Láng Hạ",
]


# LƯU Ý khi viết bước bằng lambda: biến của vòng lặp phải truyền qua tham số mặc định (a=a, ad=addr),
# nếu không lambda sẽ đọc giá trị CUỐI CÙNG của biến lúc chạy (lỗi "late binding" của Python).


@dataclass
class Account:
    """Một tài khoản mô phỏng và nhãn thật của nó."""

    key: str
    persona: str
    group: str
    is_abuse: bool
    device: str
    ip: str
    hard_negative: bool = False
    unseen: bool = False
    # Lịch sử tạo sẵn trong quá khứ (dữ liệu seed): tuổi tài khoản và kết quả các đơn COD cũ
    age_days: float | None = None
    history: list[str] = field(default_factory=list)
    user_id: int | None = None
    client: object | None = None


@dataclass
class Group:
    """Một "người điều khiển": khách lẻ, một gia đình, hay một farm. Các bước trong nhóm chạy tuần tự."""

    name: str
    accounts: list[Account]
    steps: list[Callable] = field(default_factory=list)


def _address(rng: random.Random, tag: str) -> dict:
    return {
        "recipient_name": f"Khách {tag}", "phone": f"09{rng.randrange(10**7, 10**8)}",
        "line": f"{rng.randint(1, 400)} Phố {tag}", "ward": f"Phường {rng.randint(1, 20)}",
        "district": f"Quận {rng.randint(1, 12)}", "province": rng.choice(["Hà Nội", "TP Hồ Chí Minh", "Đà Nẵng"]),
    }


def _ip(rng: random.Random) -> str:
    return f"{rng.randint(11, 220)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def build_population(dataset: str, rng: random.Random, scale: float, actions) -> list[Group]:
    """Tạo các nhóm với hành vi theo persona. `actions` là đối tượng cung cấp thao tác gọi API (runner)."""
    cfg = DATASETS[dataset]
    groups: list[Group] = []
    counter = iter(range(1, 10**6))

    def n_of(key: str) -> int:
        return max(1, round(cfg[key]["n"] * scale)) if key in cfg else 0

    def acc(persona, group, abuse, device=None, ip=None, **kw) -> Account:
        i = next(counter)
        return Account(key=f"{persona}{i}", persona=persona, group=group, is_abuse=abuse,
                       device=device or f"sim-dev-{i}", ip=ip or _ip(rng), **kw)

    # ---- Người dùng hợp lệ ----
    p = cfg["normal_new"]
    for g in range(n_of("normal_new")):
        a = acc("normal_new", f"normal_new{g}", False)
        grp = Group(a.group, [a])
        cod = rng.random() < p["cod_prob"]
        voucher = rng.random() < p["voucher_prob"]
        grp.steps = [
            lambda a=a: actions.register(a),
            *[lambda a=a: actions.view(a, rng.choice(CHEAP + MID)) for _ in range(rng.randint(1, 3))],
            lambda a=a: actions.add(a, rng.choice(CHEAP + MID), 1),
            *([lambda a=a: actions.voucher(a, "TANTHU")] if voucher else []),
            lambda a=a, cod=cod: actions.checkout(a, _address(rng, a.key), cod=cod, abandon_if_no_cod=False),
        ]
        groups.append(grp)

    p = cfg["loyal"]
    for g in range(n_of("loyal")):
        delivered = rng.randint(*p["delivered"])
        failed = round(delivered * rng.uniform(*p["fail_rate"]))
        a = acc("loyal", f"loyal{g}", False, age_days=rng.uniform(60, 400),
                history=["DELIVERED"] * delivered + ["DELIVERY_FAILED"] * failed)
        sku, qty = rng.choice(HIGH) if rng.random() < p["high_value_prob"] else (rng.choice(CHEAP + MID), 1)
        grp = Group(a.group, [a])
        grp.steps = [lambda a=a: actions.login(a), lambda a=a, s=sku: actions.view(a, s),
                     lambda a=a, s=sku, q=qty: actions.add(a, s, q),
                     lambda a=a: actions.checkout(a, _address(rng, a.key), cod=True, abandon_if_no_cod=False)]
        groups.append(grp)

    # ---- Hard negative: hợp lệ nhưng dễ bị nhầm ----
    p = cfg["family"]
    for g in range(n_of("family")):
        ip, addr = _ip(rng), _address(rng, f"GiaDinh{g}")
        members = [acc("family", f"family{g}", False, ip=ip, hard_negative=True)
                   for _ in range(rng.randint(*p["size"]))]
        grp = Group(f"family{g}", members)
        for a in members:
            grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, rng.choice(CHEAP)),
                          lambda a=a: actions.add(a, rng.choice(CHEAP), 1),
                          lambda a=a: actions.voucher(a, "TANTHU"),
                          lambda a=a, ad=addr: actions.checkout(a, ad, cod=rng.random() < 0.5, abandon_if_no_cod=False)]
        groups.append(grp)

    for g in range(n_of("new_high_value")):
        a = acc("new_high_value", f"new_high_value{g}", False, hard_negative=True)
        sku, qty = rng.choice(HIGH)
        groups.append(Group(a.group, [a], [
            lambda a=a: actions.register(a),
            *[lambda a=a: actions.view(a, rng.choice(MID)) for _ in range(2)],
            lambda a=a, s=sku: actions.view(a, s), lambda a=a, s=sku, q=qty: actions.add(a, s, q),
            lambda a=a: actions.checkout(a, _address(rng, a.key), cod=True, abandon_if_no_cod=False),
        ]))

    p = cfg["repeat_buyer"]
    for g in range(n_of("repeat_buyer")):
        a = acc("repeat_buyer", f"repeat_buyer{g}", False, hard_negative=True, age_days=rng.uniform(90, 600),
                history=["DELIVERED"] * rng.randint(10, 30))
        addr = _address(rng, a.key)
        steps = [lambda a=a: actions.login(a)]
        for _ in range(p["orders"]):
            steps += [lambda a=a: actions.view(a, rng.choice(CHEAP)), lambda a=a: actions.add(a, rng.choice(CHEAP), 1),
                      lambda a=a, ad=addr: actions.checkout(a, ad, cod=True, abandon_if_no_cod=False)]
        groups.append(Group(a.group, [a], steps))

    # ---- Lạm dụng ----
    p = cfg["farm"]
    for g in range(n_of("farm")):
        n_dev = rng.randint(*p["devices"])
        devices = [f"sim-farm{g}-dev{d}" for d in range(n_dev)]
        rotate = rng.random() < p["rotate_ip_prob"]
        base_ip = _ip(rng)
        members = [acc("farm", f"farm{g}", True, device=devices[i % n_dev], ip=_ip(rng) if rotate else base_ip)
                   for i in range(rng.randint(*p["accounts"]))]
        grp = Group(f"farm{g}", members)
        for a in members:
            addr = {**_address(rng, "Farm"), "district": "Ba Đình", "province": "Hà Nội", "ward": "Thành Công",
                    "line": rng.choice(FARM_ADDRESS_VARIANTS) if p["address_variants"] else FARM_ADDRESS_VARIANTS[0]}
            grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.add(a, "AU-001", 1),
                          lambda a=a: actions.voucher(a, "TANTHU"),
                          lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
        groups.append(grp)

    p = cfg["cod_bomber"]
    for g in range(n_of("cod_bomber")):
        finished = rng.randint(*p["finished"])
        failed = max(1, round(finished * rng.uniform(*p["fail_rate"])))
        outcomes = ["DELIVERY_FAILED"] * failed + ["DELIVERED"] * (finished - failed)
        rng.shuffle(outcomes)
        a = acc("cod_bomber", f"cod_bomber{g}", True, age_days=rng.uniform(30, 200), history=outcomes)
        sku = rng.choice(CHEAP + MID)
        groups.append(Group(a.group, [a], [
            lambda a=a: actions.login(a), lambda a=a, s=sku: actions.view(a, s), lambda a=a, s=sku: actions.add(a, s, 1),
            lambda a=a: actions.checkout(a, _address(rng, a.key), cod=True, abandon_if_no_cod=True),
        ]))

    # ---- Biến thể chưa biết (chỉ tập test) ----
    if "farm_spread" in cfg:
        for g in range(n_of("farm_spread")):
            members = [acc("farm_spread", f"farm_spread{g}", True, unseen=True)
                       for _ in range(rng.randint(*cfg["farm_spread"]["accounts"]))]
            grp = Group(f"farm_spread{g}", members)
            for a in members:
                addr = {**_address(rng, "Farm"), "district": "Thanh Xuân", "province": "Hà Nội", "ward": "Khương Mai",
                        "line": rng.choice(["Số 9 Ngõ 3 Khương Mai", "so 09 ngo 3 khuong mai", "9, Ngõ 3, Khương Mai"])}
                grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, "AU-001"),
                              lambda a=a: actions.add(a, "AU-001", 1), lambda a=a: actions.voucher(a, "TANTHU"),
                              lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
            groups.append(grp)
    if "cod_hoarder" in cfg:
        for g in range(n_of("cod_hoarder")):
            a = acc("cod_hoarder", f"cod_hoarder{g}", True, unseen=True)
            addr = _address(rng, a.key)
            steps = [lambda a=a: actions.register(a), lambda a=a: actions.view(a, rng.choice(MID))]
            for _ in range(rng.randint(*cfg["cod_hoarder"]["orders"])):
                steps += [lambda a=a: actions.add(a, rng.choice(MID), 1),
                          lambda a=a, ad=addr: actions.checkout(a, ad, cod=True, abandon_if_no_cod=True)]
            groups.append(Group(a.group, [a], steps))

    return groups
