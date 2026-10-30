"""Sinh lịch sử demo nhiều ngày trên CSDL dev, để dashboard, heatmap và biểu đồ theo ngày "có hình".

    .venv/Scripts/python -m simulator.history --days 14 --yes

Khác với bộ mô phỏng thực nghiệm (simulator/__main__.py):
- KHÔNG xóa dữ liệu: chạy CỘNG DỒN sau `python -m app.modules.lab.reset --yes`.
- Mỗi "ngày" là một đợt khách (persona của tập dev, quy mô nhỏ), thao tác qua API thật nên Risk Engine
  chấm điểm thật. Chạy xong thì dời mốc thời gian của đợt đó về đúng ngày trong quá khứ, THEO TỪNG KHÁCH
  (mọi bản ghi của một khách dời cùng một khoảng) nên thứ tự sự kiện của khách đó vẫn đúng.
- Đơn của các ngày cũ được giả lập giao hàng: khách thường giao thành công, kẻ bùng hàng giao thất bại.

Toàn bộ là DỮ LIỆU MÔ PHỎNG (email @sim.test). Chỉ chạy khi DEMO_MODE=true.
"""

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core import jobs
from app.core.config import get_settings
from app.core.db import SessionLocal, get_db
from app.core.time import utcnow
from app.main import app
from app.models import *  # noqa: F401,F403 - nạp đủ model
from app.modules.auth.models import ADMIN, ANALYST, CUSTOMER, User
from app.modules.cases import service as cases_service
from app.modules.cases.models import RiskCase
from app.modules.catalog import seed as catalog_seed
from app.modules.catalog.models import Product
from app.modules.lab.reset import add_history, make_user
from app.modules.order import service as order_service
from app.modules.order.models import Order
from simulator.personas import build_population
from simulator.runner import PASSWORD, Actions
from worker.main import register_handlers

VN = timedelta(hours=7)
# Giờ trong ngày (giờ VN) theo trọng số: khách mua nhiều vào trưa và tối
HOUR_WEIGHTS = {h: w for h, w in zip(range(24), [1, 1, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 6, 5, 5, 6, 7, 8, 9, 10, 9, 6, 3])}
# Bản ghi dời theo user_id: (bảng, cột thời gian)
BY_USER = [("orders", "created_at"), ("risk_decisions", "created_at"), ("events", "occurred_at"),
           ("addresses", "created_at")]


def _max_id(db: Session, table: str) -> int:
    return db.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table}")).scalar()


def _shift_user(db: Session, user_id: int, seconds: int, marks: dict[str, int], registered: bool) -> None:
    """Dời mọi bản ghi MỚI (id lớn hơn mốc trước đợt) của một khách đi `seconds` giây (số âm = về quá khứ)."""
    p = {"u": user_id, "s": seconds}
    if registered:
        db.execute(text("UPDATE users SET created_at = DATE_ADD(created_at, INTERVAL :s SECOND) WHERE id = :u"), p)
    for table, col in BY_USER:
        db.execute(text(f"UPDATE {table} SET {col} = DATE_ADD({col}, INTERVAL :s SECOND) "
                        f"WHERE user_id = :u AND id > :m"), {**p, "m": marks[table]})
    db.execute(text("UPDATE shipment_events se JOIN orders o ON o.id = se.order_id "
                    "SET se.occurred_at = DATE_ADD(se.occurred_at, INTERVAL :s SECOND) "
                    "WHERE o.user_id = :u AND se.id > :m"), {**p, "m": marks["shipment_events"]})
    db.execute(text("UPDATE risk_cases SET opened_at = DATE_ADD(opened_at, INTERVAL :s SECOND), "
                    "closed_at = DATE_ADD(closed_at, INTERVAL :s SECOND) "
                    "WHERE primary_user_id = :u AND id > :m"), {**p, "m": marks["risk_cases"]})
    db.execute(text("UPDATE audit_logs a JOIN risk_cases c ON a.entity_type = 'case' AND a.entity_id = c.case_code "
                    "SET a.created_at = DATE_ADD(a.created_at, INTERVAL :s SECOND) "
                    "WHERE c.primary_user_id = :u AND a.id > :m"), {**p, "m": marks["audit_logs"]})
    db.execute(text("UPDATE case_actions ca JOIN risk_cases c ON c.id = ca.case_id "
                    "SET ca.created_at = DATE_ADD(ca.created_at, INTERVAL :s SECOND) "
                    "WHERE c.primary_user_id = :u AND ca.id > :m"), {**p, "m": marks["case_actions"]})


def run(days: int, seed: int, per_day: float, progress=print, session_factory=SessionLocal) -> dict:
    rng = random.Random(seed)
    register_handlers()
    db = session_factory()
    # Kho tạm thời rất lớn để lịch sử không làm hết hàng; chạy xong seed lại tồn kho chuẩn
    db.execute(text("UPDATE products SET stock = 100000"))
    db.commit()
    skus = {p.sku: p for p in db.scalars(select(Product))}
    admin = db.scalar(select(User).where(User.role == ADMIN))
    analyst = db.scalar(select(User).where(User.role == ANALYST))
    if admin is None or analyst is None:
        raise SystemExit("Chưa có tài khoản admin: chạy demo reset trước.")

    def _get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db
    totals = {"accounts": 0, "orders": 0}
    try:
        actions = Actions(db, skus)
        today_vn = (utcnow() + VN).date()
        for d in range(days, 0, -1):
            day_vn = today_vn - timedelta(days=d)
            marks = {t: _max_id(db, t) for t in
                     ("orders", "risk_decisions", "events", "addresses", "shipment_events", "risk_cases", "case_actions",
                      "audit_logs")}
            groups = build_population("dev", rng, per_day, actions)
            accounts = [a for g in groups for a in g.accounts]
            for a in accounts:  # khóa, thiết bị riêng cho từng ngày để không "dính" sang ngày khác
                a.key = f"d{d}-{a.key}"
                a.device = f"d{d}-{a.device}"
            old = [a for a in accounts if a.age_days is not None]
            for a in old:
                u = make_user(db, f"{a.key}@sim.test", a.key, CUSTOMER, PASSWORD, timedelta(days=a.age_days + d))
                if a.history:
                    add_history(db, u, skus["SM-002"], a.history)
            db.commit()

            pending = [list(g.steps) for g in groups]
            while pending:
                i = rng.randrange(len(pending))
                pending[i].pop(0)()
                if not pending[i]:
                    pending.pop(i)
            db.rollback()
            jobs.run_all(db)  # mở case cho các quyết định cần người xem xét

            # Giả lập giao hàng cho đơn của ngày này (trừ đơn đang giữ chờ duyệt)
            bombers = {a.user_id for a in accounts if a.persona in ("cod_bomber", "cod_hoarder")}
            for order in db.scalars(select(Order).where(Order.id > marks["orders"], Order.status == "CONFIRMED")):
                order_service.update_shipment(db, admin, order.order_code, "SHIPPING", "Mô phỏng")
                failed = order.user_id in bombers and order.payment_method == "COD"
                order_service.update_shipment(db, admin, order.order_code,
                                              "DELIVERY_FAILED" if failed else "DELIVERED", "Mô phỏng")
            db.rollback()

            # Case của các ngày cũ coi như đã được analyst xử lý (lạm dụng thật -> xác nhận, khách thật -> gỡ);
            # chỉ để mở case của ngày gần nhất, giống một hàng đợi thực tế
            resolved: list[int] = []
            if d >= 2:
                abusers = {a.user_id for a in accounts if a.is_abuse}
                for case in db.scalars(select(RiskCase).where(RiskCase.id > marks["risk_cases"],
                                                              RiskCase.status == "OPEN")).all():
                    cases_service.claim(db, analyst, case.case_code)
                    abuse = case.primary_user_id in abusers
                    cases_service.resolve(db, analyst, case.case_code,
                                          "CONFIRMED_ABUSE" if abuse else "CLEARED",
                                          "Mô phỏng: " + ("xác nhận lạm dụng sau khi đối chiếu tài khoản liên kết"
                                                          if abuse else "khách hợp lệ, đã xác minh"))
                    resolved.append(case.id)
            db.rollback()

            # Dời thời gian: mỗi khách một thời điểm ngẫu nhiên trong ngày (giờ VN, theo trọng số giờ)
            now = utcnow()
            for a in accounts:
                if a.user_id is None:
                    continue
                hour = rng.choices(list(HOUR_WEIGHTS), weights=list(HOUR_WEIGHTS.values()))[0]
                target = datetime(day_vn.year, day_vn.month, day_vn.day, hour, rng.randrange(60), rng.randrange(60)) - VN
                _shift_user(db, a.user_id, int((target - now).total_seconds()), marks, registered=a.age_days is None)
            # Thời gian xử lý case: từ 20 phút đến 6 giờ sau khi mở (thay vì vài giây lúc chạy script)
            for case_id in resolved:
                delay = rng.randint(20 * 60, 6 * 3600)
                q = {"c": case_id, "s": delay}
                db.execute(text("UPDATE risk_cases SET closed_at = DATE_ADD(closed_at, INTERVAL :s SECOND) WHERE id = :c"), q)
                db.execute(text("UPDATE case_actions SET created_at = DATE_ADD(created_at, INTERVAL :s SECOND) "
                                "WHERE case_id = :c AND action IN ('claim', 'resolve')"), q)
            db.commit()
            n_orders = db.execute(text("SELECT COUNT(*) FROM orders WHERE id > :m"), {"m": marks["orders"]}).scalar()
            totals["accounts"] += len(accounts)
            totals["orders"] += n_orders
            progress(f"  {day_vn:%d/%m}: {len(accounts)} khách, {n_orders} đơn")
        catalog_seed.seed(db)  # trả tồn kho về số chuẩn
        totals["server_errors"] = actions.errors[:5]
        return totals
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        db.close()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Sinh lịch sử demo nhiều ngày (cộng dồn, không xóa dữ liệu)")
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--per-day", type=float, default=0.07, help="quy mô mỗi ngày so với tập dev (0.07 ≈ 15 khách)")
    parser.add_argument("--yes", action="store_true", help="xác nhận ghi thêm dữ liệu mô phỏng vào CSDL dev")
    args = parser.parse_args()
    if not get_settings().demo_mode:
        print("Chỉ chạy khi DEMO_MODE=true.", file=sys.stderr)
        return 1
    if not args.yes:
        print("Thêm --yes để xác nhận ghi dữ liệu mô phỏng vào CSDL dev.", file=sys.stderr)
        return 1
    print(f"Sinh lịch sử {args.days} ngày (seed {args.seed})…")
    totals = run(args.days, args.seed, args.per_day)
    print(f"Xong: {totals['accounts']} khách, {totals['orders']} đơn; lỗi server: {len(totals['server_errors'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
