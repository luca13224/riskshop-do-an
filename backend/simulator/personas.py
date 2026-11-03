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

# ---- Bộ dữ liệu cho bộ luật v2 (2026-10-31). Giữ nguyên "dev"/"test" ở trên để kết quả v1 tái lập được. ----
# farm_spread giờ là kiểu ĐÃ BIẾT (đã thấy ở test v1, R11 được thiết kế cho nó) nên nằm cả ở dev_v2 để hiệu chỉnh.
# roommates_4g: hard negative MỚI, nhóm ở trọ chung nhà, mỗi người dùng 4G riêng (độ phân tán mạng cao như farm).
# farm_multi_drop: biến thể CHƯA BIẾT MỚI, định nghĩa trước khi chạy và không tinh chỉnh theo nó:
# farm phân tán nhưng gom hàng về 2–3 điểm nhận khác nhau, nên mỗi địa chỉ chỉ có vài tài khoản.
# per_group_address: mỗi farm một địa chỉ riêng (ở dev/test v1, mọi farm cùng loại vô tình giao về MỘT địa chỉ,
# khiến các farm độc lập gộp thành một cụm lớn, dễ phát hiện hơn thực tế).
DATASETS["dev_v2"] = {
    **DATASETS["dev"],
    "farm": {**DATASETS["dev"]["farm"], "per_group_address": True},
    "farm_spread": {"n": 4, "accounts": (4, 7), "unseen": False, "per_group_address": True},
    "roommates_4g": {"n": 6, "size": (3, 6)},
}
DATASETS["test_v2"] = {
    **DATASETS["test"],
    "farm": {**DATASETS["test"]["farm"], "per_group_address": True},
    "farm_spread": {"n": 5, "accounts": (5, 8), "unseen": False, "per_group_address": True},
    "cod_hoarder": {"n": 6, "orders": (3, 4), "unseen": False},  # đã thấy ở test v1, v2 chưa xử lý
    "roommates_4g": {"n": 8, "size": (3, 6)},
    "farm_multi_drop": {"n": 5, "accounts": (6, 9), "drops": (2, 3)},
}

# ---- Bộ dữ liệu cho mục tiêu O7 (2026-11-03, ADR-011): né lệnh khóa bằng tài khoản mới. ----
# Mỗi nhóm có một tài khoản NGUỒN: đăng ký, mua một đơn, rồi bị nhân viên khóa vô thời hạn (purchase_ban).
# Tài khoản nguồn không nằm trong dân số được chấm (nó là bối cảnh, không phải đối tượng đo).
# - ban_evader (đã biết): tài khoản mới chung >= 2 điểm (thiết bị, SĐT nhận hàng, địa chỉ) với nguồn, dùng mã người mới.
# - ban_evader_spam (đã biết): cùng máy với nguồn, mỗi tài khoản một địa chỉ / SĐT mới, tạo liên tiếp để gom mã.
# - ban_evader_one_link (CHƯA BIẾT): máy mới, địa chỉ mới, chỉ giữ SĐT nhận hàng cũ, một tài khoản, không spam.
#   Theo thiết kế ADR-011 trường hợp này chỉ bị trừ điểm + mở case, không bị khóa: đo để thấy giới hạn.
# - banned_relative (hard negative): người nhà dùng chung máy với nguồn, địa chỉ / SĐT riêng, mua bình thường.
# Tham số ở test rộng hơn dev (số tài khoản, tổ hợp điểm chung). Định nghĩa trước khi chạy, không tinh chỉnh theo test.
EVADER_LINKS = ("device", "phone", "address")
DATASETS["dev_v3"] = {
    **DATASETS["dev_v2"],
    "ban_evader": {"n": 5, "accounts": (1, 2), "links": [("device", "address")]},
    "ban_evader_spam": {"n": 3, "accounts": (2, 3)},
    "banned_relative": {"n": 5},
}
DATASETS["test_v3"] = {
    **DATASETS["test_v2"],
    "ban_evader": {"n": 8, "accounts": (1, 3),
                   "links": [("device", "address"), ("device", "phone"), ("phone", "address"), EVADER_LINKS]},
    "ban_evader_spam": {"n": 4, "accounts": (2, 4)},
    "ban_evader_one_link": {"n": 6},
    "banned_relative": {"n": 8},
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
            *([lambda a=a: actions.voucher(a, "NGUOIMOI")] if voucher else []),
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
                          lambda a=a: actions.voucher(a, "NGUOIMOI"),
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
        variants = _drop_variants(g, "Láng Hạ") if p.get("per_group_address") else FARM_ADDRESS_VARIANTS
        for a in members:
            addr = {**_address(rng, "Farm"), "district": "Ba Đình", "province": "Hà Nội", "ward": "Thành Công",
                    "line": rng.choice(variants) if p["address_variants"] else variants[0]}
            grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.add(a, "AU-001", 1),
                          lambda a=a: actions.voucher(a, "NGUOIMOI"),
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
            members = [acc("farm_spread", f"farm_spread{g}", True, unseen=cfg["farm_spread"].get("unseen", True))
                       for _ in range(rng.randint(*cfg["farm_spread"]["accounts"]))]
            grp = Group(f"farm_spread{g}", members)
            variants = (_drop_variants(100 + g, "Khương Mai") if cfg["farm_spread"].get("per_group_address")
                        else ["Số 9 Ngõ 3 Khương Mai", "so 09 ngo 3 khuong mai", "9, Ngõ 3, Khương Mai"])
            for a in members:
                addr = {**_address(rng, "Farm"), "district": "Thanh Xuân", "province": "Hà Nội", "ward": "Khương Mai",
                        "line": rng.choice(variants)}
                grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, "AU-001"),
                              lambda a=a: actions.add(a, "AU-001", 1), lambda a=a: actions.voucher(a, "NGUOIMOI"),
                              lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
            groups.append(grp)
    if "cod_hoarder" in cfg:
        for g in range(n_of("cod_hoarder")):
            a = acc("cod_hoarder", f"cod_hoarder{g}", True, unseen=cfg["cod_hoarder"].get("unseen", True))
            addr = _address(rng, a.key)
            steps = [lambda a=a: actions.register(a), lambda a=a: actions.view(a, rng.choice(MID))]
            for _ in range(rng.randint(*cfg["cod_hoarder"]["orders"])):
                steps += [lambda a=a: actions.add(a, rng.choice(MID), 1),
                          lambda a=a, ad=addr: actions.checkout(a, ad, cod=True, abandon_if_no_cod=True)]
            groups.append(Group(a.group, [a], steps))

    # ---- Bộ v2 ----
    if "roommates_4g" in cfg:  # hard negative: chung nhà, mỗi người một máy và một mạng 4G riêng
        for g in range(n_of("roommates_4g")):
            addr = _address(rng, f"NhaTro{g}")
            members = [acc("roommates_4g", f"roommates_4g{g}", False, hard_negative=True)
                       for _ in range(rng.randint(*cfg["roommates_4g"]["size"]))]
            grp = Group(f"roommates_4g{g}", members)
            for a in members:
                grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, rng.choice(CHEAP)),
                              lambda a=a: actions.add(a, rng.choice(CHEAP), 1),
                              lambda a=a: actions.voucher(a, "NGUOIMOI"),
                              lambda a=a, ad=addr: actions.checkout(a, ad, cod=rng.random() < 0.5,
                                                                    abandon_if_no_cod=False)]
            groups.append(grp)
    if "farm_multi_drop" in cfg:  # biến thể chưa biết: farm phân tán, gom hàng về 2–3 điểm nhận
        p = cfg["farm_multi_drop"]
        for g in range(n_of("farm_multi_drop")):
            drops = [_drop_variants(200 + g * 10 + k, "Hoàng Mai")[0] for k in range(rng.randint(*p["drops"]))]
            members = [acc("farm_multi_drop", f"farm_multi_drop{g}", True, unseen=True)
                       for _ in range(rng.randint(*p["accounts"]))]
            grp = Group(f"farm_multi_drop{g}", members)
            for i, a in enumerate(members):
                addr = {**_address(rng, "Farm"), "district": "Hoàng Mai", "province": "Hà Nội", "ward": "Mai Động",
                        "line": drops[i % len(drops)]}
                grp.steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, "AU-001"),
                              lambda a=a: actions.add(a, "AU-001", 1), lambda a=a: actions.voucher(a, "NGUOIMOI"),
                              lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
            groups.append(grp)

    # ---- Bộ v3: né lệnh khóa (O7) ----
    def banned_source(tag: str, device: str) -> tuple[Account, dict, list[Callable]]:
        src = acc("banned_source", tag, True, device=device)
        addr = _address(rng, f"Ban{tag}")
        steps = [lambda s=src: actions.register(s), lambda s=src: actions.view(s, rng.choice(CHEAP)),
                 lambda s=src: actions.add(s, rng.choice(CHEAP), 1),
                 lambda s=src, ad=addr: actions.checkout(s, ad, cod=False, abandon_if_no_cod=False),
                 lambda s=src: actions.ban(s)]
        return src, addr, steps

    if "ban_evader" in cfg:
        p = cfg["ban_evader"]
        for g in range(n_of("ban_evader")):
            tag = f"ban_evader{g}"
            src, src_addr, steps = banned_source(tag, f"sim-ban{g}-dev")
            members = []
            for _ in range(rng.randint(*p["accounts"])):
                links = rng.choice(p["links"])
                a = acc("ban_evader", tag, True, device=src.device if "device" in links else None)
                addr = _address(rng, a.key)
                if "address" in links:
                    addr = {**src_addr, "phone": addr["phone"]}
                if "phone" in links:
                    addr = {**addr, "phone": src_addr["phone"]}
                members.append(a)
                steps += [lambda a=a: actions.register(a), lambda a=a: actions.add(a, "AU-001", 1),
                          lambda a=a: actions.voucher(a, "NGUOIMOI"),
                          lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
            groups.append(Group(tag, members, steps))
    if "ban_evader_spam" in cfg:
        for g in range(n_of("ban_evader_spam")):
            tag = f"ban_evader_spam{g}"
            src, _, steps = banned_source(tag, f"sim-banspam{g}-dev")
            members = [acc("ban_evader_spam", tag, True, device=src.device)
                       for _ in range(rng.randint(*cfg["ban_evader_spam"]["accounts"]))]
            for a in members:
                steps += [lambda a=a: actions.register(a), lambda a=a: actions.add(a, "AU-001", 1),
                          lambda a=a: actions.voucher(a, "NGUOIMOI"),
                          lambda a=a: actions.checkout_if_voucher(a, _address(rng, a.key))]
            groups.append(Group(tag, members, steps))
    if "ban_evader_one_link" in cfg:
        for g in range(n_of("ban_evader_one_link")):
            tag = f"ban_evader_one_link{g}"
            src, src_addr, steps = banned_source(tag, f"sim-ban1-{g}-dev")
            a = acc("ban_evader_one_link", tag, True, unseen=True)
            addr = {**_address(rng, a.key), "phone": src_addr["phone"]}
            steps += [lambda a=a: actions.register(a), lambda a=a: actions.view(a, "AU-001"),
                      lambda a=a: actions.add(a, "AU-001", 1), lambda a=a: actions.voucher(a, "NGUOIMOI"),
                      lambda a=a, ad=addr: actions.checkout_if_voucher(a, ad)]
            groups.append(Group(tag, [a], steps))
    if "banned_relative" in cfg:
        for g in range(n_of("banned_relative")):
            tag = f"banned_relative{g}"
            src, _, steps = banned_source(tag, f"sim-banrel{g}-dev")
            a = acc("banned_relative", tag, False, device=src.device, ip=src.ip, hard_negative=True)
            sku = rng.choice(CHEAP + MID)
            steps += [lambda a=a: actions.register(a), lambda a=a, s=sku: actions.view(a, s),
                      lambda a=a, s=sku: actions.add(a, s, 1), lambda a=a: actions.voucher(a, "NGUOIMOI"),
                      lambda a=a: actions.checkout(a, _address(rng, a.key), cod=rng.random() < 0.5,
                                                   abandon_if_no_cod=False)]
            groups.append(Group(tag, [a], steps))

    return groups


def _drop_variants(k: int, street: str) -> list[str]:
    """Một địa chỉ riêng cho nhóm thứ k, viết theo 3 kiểu khác nhau nhưng chuẩn hóa về cùng một địa chỉ."""
    n, lane = 5 + k * 7, 2 + k
    return [f"Số {n} Ngõ {lane} {street}", f"so 0{n} ngo {lane} {street.lower()}", f"{n}, Ngõ {lane}, {street}"]
