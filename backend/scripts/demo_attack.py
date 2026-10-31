"""Diễn cảnh tấn công cho buổi demo: gọi THẲNG API (bỏ qua giao diện), đúng như kẻ gian dùng công cụ.

Chỉ dùng trên máy local khi chạy demo. Backend phải đang chạy ở http://127.0.0.1:8000.

    # Cảnh 5c: khách đã bị ẩn COD vẫn cố gửi đơn COD nhiều lần -> lần thứ 4 bị chặn và khóa mua 24 giờ
    .venv/Scripts/python scripts/demo_attack.py spam-cod khang@shop.test --times 4

    # Cảnh 5e: (sau khi Risk Manager khóa vô thời hạn tài khoản trên trong Console)
    # tạo tài khoản mới trên CÙNG máy rồi spam mã NGUOIMOI -> bị khóa thanh toán 30 ngày (ADR-011)
    .venv/Scripts/python scripts/demo_attack.py evade

Mật khẩu tài khoản demo đọc từ backend/.env.accounts (file local, không có trên GitHub).
"""

import argparse
import secrets
import sys
import uuid
from pathlib import Path

import httpx

API = "http://127.0.0.1:8000/api"
DEVICE = "demo-attacker-01"  # cùng một "máy" cho cả hai cảnh, để cảnh evade nối được với tài khoản bị khóa
ACCOUNTS_FILE = Path(__file__).resolve().parents[1] / ".env.accounts"
ADDRESS = {"recipient_name": "Người nhận", "phone": "0909000999", "line": "27 Ngõ Demo",
           "ward": "Phường Demo", "district": "Quận Demo", "province": "Hà Nội"}


def password_of(email: str) -> str:
    for line in ACCOUNTS_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{email}="):
            return line.split("=", 1)[1]
    sys.exit(f"Không thấy {email} trong {ACCOUNTS_FILE} (chạy demo reset để tạo lại).")


def client() -> httpx.Client:
    return httpx.Client(base_url=API, headers={"X-Device-Id": DEVICE}, timeout=15)


def show(label: str, r: httpx.Response) -> None:
    body = r.json() if r.content else {}
    detail = body["error"]["message"] if "error" in body else body.get("order_code") or body.get("voucher") or ""
    print(f"  {label}: {r.status_code} {detail}")


def add_cheap_item(c: httpx.Client) -> None:
    items = c.get("/products", params={"sort": "price_asc", "min_price": 250_000}).json()["items"]
    c.post("/cart/items", json={"product_id": items[0]["id"], "quantity": 1})


def spam_cod(email: str, times: int) -> None:
    with client() as c:
        r = c.post("/auth/login", json={"email": email, "password": password_of(email)})
        if r.status_code != 200:
            sys.exit(f"Đăng nhập {email} thất bại: {r.text}")
        add_cheap_item(c)
        print(f"Gửi {times} đơn COD từ {email} (thiết bị {DEVICE}):")
        for i in range(1, times + 1):
            show(f"lần {i}", c.post("/orders/checkout", json={"address": ADDRESS, "payment_method": "COD"},
                                     headers={"Idempotency-Key": str(uuid.uuid4())}))


def evade() -> None:
    email = f"acc-moi-{secrets.token_hex(3)}@demo.test"
    with client() as c:
        r = c.post("/auth/register", json={"email": email, "password": secrets.token_urlsafe(12),
                                           "full_name": "Tài khoản mới"})
        print(f"Tạo tài khoản mới {email} trên thiết bị {DEVICE}: {r.status_code}")
        add_cheap_item(c)
        for i in (1, 2):
            show(f"áp NGUOIMOI lần {i}", c.post("/cart/voucher", json={"code": "NGUOIMOI"}))
        show("đặt hàng trả trước", c.post("/orders/checkout", json={"address": ADDRESS, "payment_method": "PREPAID"},
                                           headers={"Idempotency-Key": str(uuid.uuid4())}))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Diễn cảnh tấn công cho buổi demo")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("spam-cod", help="cố gửi đơn COD nhiều lần sau khi bị từ chối")
    p.add_argument("email")
    p.add_argument("--times", type=int, default=4)
    sub.add_parser("evade", help="tạo tài khoản mới trên cùng máy và spam mã người mới")
    args = parser.parse_args()
    if args.cmd == "spam-cod":
        spam_cod(args.email, args.times)
    else:
        evade()


if __name__ == "__main__":
    main()
