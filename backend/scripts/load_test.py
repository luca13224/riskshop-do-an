"""Đo độ trễ đặt hàng khi nhiều người dùng cùng lúc (kịch bản E2, mục tiêu O5 / NFR-01).

Chạy trên CSDL MÔ PHỎNG (SIM_DATABASE_URL, bị xóa sạch ở bước setup), không đụng dữ liệu demo.
Không chạy cùng lúc với simulator.

    1) .venv/Scripts/python scripts/load_test.py setup
       Xóa CSDL mô phỏng, nạp lại sản phẩm / voucher / luật (giống bước chuẩn bị của simulator).
    2) Mở cửa sổ khác, chạy backend trỏ vào CSDL mô phỏng (cổng 8001), ví dụ trong Git Bash:
       DATABASE_URL="$(grep ^SIM_DATABASE_URL .env | cut -d= -f2-)" .venv/Scripts/python -m uvicorn app.main:app --port 8001
    3) .venv/Scripts/python scripts/load_test.py run --levels 1 10 50 --requests 200 --rounds 3

Mỗi "người dùng ảo" có tài khoản và thiết bị riêng, lặp: thêm 1 sản phẩm vào giỏ → đặt hàng trả trước.
Đo hai thứ: (a) thời gian cả request POST /api/orders/checkout phía client; (b) thời gian chấm điểm Risk Engine
(cột risk_decisions.latency_ms của các quyết định place_order trong lần đo). Một tiến trình uvicorn, một máy:
đây là phép đo trên máy phát triển, không phải đo năng lực hệ thống production.
"""

import argparse
import asyncio
import json
import os
import platform
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

ADDRESS = {"recipient_name": "Khach tai", "phone": "0900000000", "line": "1 Duong Thu", "ward": "P1",
           "district": "Q1", "province": "Ha Noi"}


def load_url() -> str:
    from app.core.config import get_settings
    url = get_settings().sim_database_url
    if not url or "sim" not in make_url(url).database:
        raise SystemExit("Thiếu SIM_DATABASE_URL (phải trỏ tới CSDL có chữ 'sim', vì bước setup sẽ XÓA dữ liệu).")
    return url


def setup() -> None:
    from sqlalchemy.orm import Session

    from simulator.runner import _prepare
    with Session(create_engine(load_url())) as db:
        _prepare(db)  # xóa sạch, nạp sản phẩm / voucher / luật, tồn kho lớn
    print("Đã chuẩn bị CSDL mô phỏng. Bước 2: chạy backend trỏ vào nó (xem đầu file).")


async def make_user(base: str, i: int, tag: str) -> tuple[httpx.AsyncClient, int]:
    c = httpx.AsyncClient(base_url=base, timeout=60, headers={"X-Device-Id": f"load-{tag}-{i}"})
    r = await c.post("/api/auth/register", json={"email": f"load-{tag}-{i}@load.test", "password": "taitai123",
                                                 "full_name": f"Tai {i}"})
    r.raise_for_status()
    products = (await c.get("/api/products", params={"page_size": 1})).json()
    return c, products["items"][0]["id"]


async def worker(c: httpx.AsyncClient, product_id: int, jobs: asyncio.Queue, out: list, statuses: dict) -> None:
    while True:
        try:
            jobs.get_nowait()
        except asyncio.QueueEmpty:
            return
        await c.post("/api/cart/items", json={"product_id": product_id, "quantity": 1})
        t0 = time.perf_counter()
        r = await c.post("/api/orders/checkout", json={"address": ADDRESS, "payment_method": "PREPAID"},
                         headers={"Idempotency-Key": str(uuid.uuid4())})
        out.append((time.perf_counter() - t0) * 1000)
        statuses[r.status_code] = statuses.get(r.status_code, 0) + 1


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, max(0, int(round(p / 100 * len(xs))) - 1))], 1)


def summarize(xs: list[float]) -> dict:
    return {"n": len(xs), "p50": pct(xs, 50), "p95": pct(xs, 95), "p99": pct(xs, 99),
            "mean": round(statistics.fmean(xs), 1)}


async def run_level(base: str, users: int, requests: int, tag: str) -> dict:
    clients = await asyncio.gather(*(make_user(base, i, tag) for i in range(users)))
    jobs: asyncio.Queue = asyncio.Queue()
    for _ in range(requests):
        jobs.put_nowait(1)
    out: list[float] = []
    statuses: dict[int, int] = {}
    engine = create_engine(load_url())
    with engine.connect() as conn:  # created_at chỉ lưu đến giây, nên tách lần đo theo id
        first_id = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM risk_decisions")).scalar_one()
    t0 = time.perf_counter()
    await asyncio.gather(*(worker(c, pid, jobs, out, statuses) for c, pid in clients))
    wall = time.perf_counter() - t0
    for c, _ in clients:
        await c.aclose()
    with engine.connect() as conn:
        scoring = [row[0] for row in conn.execute(text(
            "SELECT latency_ms FROM risk_decisions WHERE context = 'place_order' AND id > :i"), {"i": first_id})]
    return {"users": users, "checkout_ms": summarize(out), "scoring_ms": summarize(scoring) if scoring else None,
            "throughput_rps": round(len(out) / wall, 1), "statuses": statuses}


async def run(base: str, levels: list[int], requests: int, rounds: int, out_path: Path | None) -> None:
    results = []
    for users in levels:
        for rnd in range(1, rounds + 1):
            tag = f"{users}u{rnd}-{uuid.uuid4().hex[:6]}"
            res = await run_level(base, users, requests, tag)
            res["round"] = rnd
            results.append(res)
            print(json.dumps(res, ensure_ascii=False))
    report = {"created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "machine": {"os": platform.platform(), "cpu": platform.processor(), "cores": os.cpu_count(),
                          "python": platform.python_version()},
              "server": "1 tiến trình uvicorn, MariaDB XAMPP cùng máy", "requests_per_round": requests,
              "results": results}
    if out_path:
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Đã ghi", out_path)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Đo độ trễ đặt hàng khi nhiều người dùng cùng lúc")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    p = sub.add_parser("run")
    p.add_argument("--base", default="http://127.0.0.1:8001")
    p.add_argument("--levels", type=int, nargs="+", default=[1, 10, 50])
    p.add_argument("--requests", type=int, default=200)
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.cmd == "setup":
        setup()
    else:
        asyncio.run(run(args.base, args.levels, args.requests, args.rounds, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
