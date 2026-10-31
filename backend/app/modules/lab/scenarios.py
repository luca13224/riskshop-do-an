"""Các kịch bản của Attack Lab (DEMO_SCRIPT.md, cảnh 2, 4, 5).

Mỗi kịch bản là một hàm nhận Runner, gọi API thật qua HTTP như một khách hàng (hoặc bot),
ghi từng bước kèm KỲ VỌNG và KẾT QUẢ THỰC TẾ, cuối cùng trả về câu tóm tắt.
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

import httpx

PAUSE = 0.6  # nghỉ giữa các bước để Live Monitor kịp "nhảy" từng dòng khi demo

ADDRESS_FARM = {"recipient_name": "Nguyễn Văn Farm", "phone": "0911000111", "line": "99 Ngõ 12 Láng Hạ",
                "ward": "Thành Công", "district": "Ba Đình", "province": "Hà Nội"}
ADDRESS_FAMILY = {"recipient_name": "Gia đình Trần", "phone": "0911222333", "line": "15 Nguyễn Trãi",
                  "ward": "Thượng Đình", "district": "Thanh Xuân", "province": "Hà Nội"}


@dataclass(frozen=True)
class Scenario:
    code: str
    title: str
    scene: str
    description: str
    expected: str
    run: Callable[["Runner"], str]


class Runner:
    """Công cụ cho kịch bản: tạo "khách hàng" ảo, ghi bước, gọi thao tác giao hàng (vai Admin)."""

    def __init__(self, client_factory: Callable[[dict], httpx.Client], record_step: Callable[[dict], None],
                 ship: Callable[[str, str], None], tag: str, pause: float = PAUSE):
        self._client_factory = client_factory
        self._record = record_step
        self.ship = ship  # ship(order_code, status): giả lập đơn vị vận chuyển
        self.tag = tag
        self.pause = pause
        self.all_ok = True

    def customer(self, name: str, device: str) -> httpx.Client:
        c = self._client_factory({"X-Device-Id": f"lab-{self.tag}-{device}"})
        email = f"{name}.{self.tag}@lab.test"
        r = c.post("/auth/register", json={"email": email, "password": "lab-matkhau-123",
                                           "full_name": f"{name.capitalize()} ({self.tag})"})
        r.raise_for_status()
        return c

    def step(self, actor: str, action: str, result: str, expected: str | None = None, ok: bool | None = None):
        if ok is False:
            self.all_ok = False
        self._record({"actor": actor, "action": action, "result": result, "expected": expected, "ok": ok})
        time.sleep(self.pause)

    @staticmethod
    def product(c: httpx.Client, query: str) -> dict:
        return c.get("/products", params={"q": query}).json()["items"][0]

    @staticmethod
    def checkout(c: httpx.Client, address: dict, method: str) -> httpx.Response:
        return c.post("/orders/checkout", json={"address": address, "payment_method": method},
                      headers={"Idempotency-Key": str(uuid.uuid4())})


def _outcome(r: httpx.Response) -> str:
    body = r.json()
    if r.status_code >= 400:
        return body["error"]["code"]
    return body.get("status") or "OK"


# ---------- Cảnh 2: farm voucher ----------

def farm_voucher(r: Runner) -> str:
    restricted = 0
    for i in range(1, 7):
        name = f"farm{i}"
        c = r.customer(name, "may-farm-01")  # cùng một thiết bị
        item = r.product(c, "Aria")
        c.post("/cart/items", json={"product_id": item["id"], "quantity": 1})
        res = c.post("/cart/voucher", json={"code": "NGUOIMOI"})
        outcome = _outcome(res)
        if outcome == "VOUCHER_NOT_APPLICABLE":
            restricted += 1
            expected_ok = i >= 3
            r.step(name, "Áp mã NGUOIMOI", "Bị gỡ voucher (thông điệp chung chung)", "Tài khoản 1–2 được dùng, từ thứ 3 bị gỡ",
                   expected_ok)
            continue
        r.step(name, "Áp mã NGUOIMOI", "Được dùng voucher", "Tài khoản 1–2 được dùng, từ thứ 3 bị gỡ", i <= 2)
        res = r.checkout(c, ADDRESS_FARM, "PREPAID")
        r.step(name, "Đặt hàng (trả trước, cùng địa chỉ farm)", _outcome(res))
    return f"{restricted}/6 tài khoản farm bị gỡ voucher; case cụm theo thiết bị sẽ được mở."


# ---------- Cảnh 4: gia đình chung Wi-Fi ----------

def family_wifi(r: Runner) -> str:
    allowed = 0
    for i in range(1, 5):
        name = f"giadinh{i}"
        c = r.customer(name, f"dien-thoai-{i}")  # mỗi người một máy
        item = r.product(c, "Aria")
        c.get(f"/products/{item['slug']}")  # người thật xem sản phẩm trước khi mua
        c.post("/cart/items", json={"product_id": item["id"], "quantity": 1})
        res = c.post("/cart/voucher", json={"code": "NGUOIMOI"})
        ok_voucher = res.status_code == 200
        r.step(name, "Áp mã NGUOIMOI (cùng Wi-Fi)", "Được dùng voucher" if ok_voucher else _outcome(res),
               "Được dùng voucher", ok_voucher)
        res = r.checkout(c, ADDRESS_FAMILY, "PREPAID")
        ok_order = res.status_code == 201
        allowed += ok_voucher and ok_order
        r.step(name, "Đặt hàng (cùng địa chỉ nhà)", _outcome(res), "CONFIRMED", ok_order)
    return f"{allowed}/4 thành viên gia đình mua thành công: IP và địa chỉ chung là tín hiệu yếu, không đủ để chặn."


# ---------- Cảnh 5b: COD giá trị cao từ tài khoản mới ----------

def cod_high_value(r: Runner) -> str:
    c = r.customer("khachmoi", "may-khachmoi")
    item = r.product(c, "ViewPro")
    c.get(f"/products/{item['slug']}")
    c.post("/cart/items", json={"product_id": item["id"], "quantity": 1})
    opts = c.get("/orders/payment-options").json()
    r.step("khachmoi", "Xem phương thức thanh toán", "Có COD" if opts["cod_allowed"] else "Không có COD",
           "Vẫn có COD (đơn sẽ được giữ để duyệt)", opts["cod_allowed"])
    res = r.checkout(c, ADDRESS_FAMILY, "COD")
    outcome = _outcome(res)
    r.step("khachmoi", f"Đặt COD {item['price']:,}đ".replace(",", "."), outcome, "PENDING_REVIEW",
           outcome == "PENDING_REVIEW")
    return "Đơn COD giá trị cao được giữ lại chờ xác minh; một case COD sẽ được mở."


# ---------- Cảnh 5a: khách có lịch sử bùng hàng COD ----------

def cod_bad_history(r: Runner) -> str:
    c = r.customer("khang", "may-khang")
    item = r.product(c, "Ổ cắm")
    c.get(f"/products/{item['slug']}")
    # Tạo lịch sử 5 đơn COD: 1 giao thành công, 4 giao thất bại (giả lập đơn vị vận chuyển)
    for n, result in enumerate(["DELIVERED"] + ["DELIVERY_FAILED"] * 4, start=1):
        c.post("/cart/items", json={"product_id": item["id"], "quantity": 1})
        res = r.checkout(c, ADDRESS_FAMILY, "COD")
        if res.status_code != 201:
            r.step("khang", f"Tạo lịch sử: đơn COD #{n}", _outcome(res), "CONFIRMED", False)
            return "Không tạo đủ lịch sử để chạy kịch bản."
        code = res.json()["order_code"]
        r.ship(code, "SHIPPING")
        r.ship(code, result)
        r.step("khang", f"Tạo lịch sử: đơn COD #{n}", "Giao thành công" if result == "DELIVERED" else "Giao thất bại")
    c.post("/cart/items", json={"product_id": item["id"], "quantity": 1})
    opts = c.get("/orders/payment-options").json()
    r.step("khang", "Xem phương thức thanh toán", "Có COD" if opts["cod_allowed"] else "COD bị ẩn",
           "COD bị ẩn", not opts["cod_allowed"])
    res = r.checkout(c, ADDRESS_FAMILY, "COD")
    r.step("khang", "Cố đặt COD bằng cách gọi thẳng API", _outcome(res), "COD_NOT_AVAILABLE",
           _outcome(res) == "COD_NOT_AVAILABLE")
    res = r.checkout(c, ADDRESS_FAMILY, "PREPAID")
    r.step("khang", "Đặt hàng trả trước", _outcome(res), "CONFIRMED", res.status_code == 201)
    return "Khách bùng hàng 4/5 đơn không còn được COD nhưng vẫn mua được bằng trả trước."


SCENARIOS: dict[str, Scenario] = {
    s.code: s
    for s in [
        Scenario("farm_voucher", "Farm voucher", "Cảnh 2",
                 "6 tài khoản mới trên CÙNG một thiết bị lần lượt áp mã tân thủ NGUOIMOI rồi đặt hàng về cùng địa chỉ.",
                 "Tài khoản 1–2 được dùng voucher; từ tài khoản thứ 3 bị gỡ voucher; mở case cụm.", farm_voucher),
        Scenario("family_wifi", "Gia đình chung Wi-Fi", "Cảnh 4",
                 "4 người trong một nhà, mỗi người một điện thoại, cùng Wi-Fi và cùng địa chỉ, mỗi người dùng 1 voucher.",
                 "Cả 4 người đều mua được (hard negative: không chặn nhầm).", family_wifi),
        Scenario("cod_high_value", "COD giá trị cao", "Cảnh 5b",
                 "Tài khoản mới tạo đặt màn hình 5,49 triệu và chọn thanh toán khi nhận hàng.",
                 "Đơn được tạo nhưng ở trạng thái Chờ xác minh; mở case COD.", cod_high_value),
        Scenario("cod_bad_history", "Lịch sử bùng hàng COD", "Cảnh 5a",
                 "Khách có 5 đơn COD trước đó, 4 đơn giao thất bại, đặt đơn mới.",
                 "COD bị ẩn và bị từ chối kể cả khi gọi thẳng API; trả trước vẫn được.", cod_bad_history),
    ]
}
