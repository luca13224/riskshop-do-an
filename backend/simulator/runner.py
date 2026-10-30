"""Bộ chạy mô phỏng và đánh giá.

1. Xóa sạch CSDL mô phỏng, seed sản phẩm, voucher, luật (luật lấy từ seed = phiên bản đã khóa trong code).
2. Tạo dân số theo persona; lịch sử quá khứ ghi thẳng vào CSDL (dữ liệu seed), hành vi hiện tại đi qua API thật.
3. Trộn ngẫu nhiên các bước giữa các nhóm (như nhiều người dùng hoạt động xen kẽ).
4. Đánh giá theo TÀI KHOẢN: hệ thống "gắn cờ" tài khoản nếu có ít nhất một quyết định khác ALLOW.
   So với nhãn thật trong sim_labels -> confusion matrix, precision, recall, FPR (khoảng tin cậy Wilson 95%).

Giới hạn (ghi trong báo cáo): thời gian bị nén (mọi hành vi hiện tại xảy ra trong vài phút chạy),
dữ liệu hoàn toàn mô phỏng, IP và thiết bị là giá trị giả lập.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.time import utcnow
from app.main import app
from app.modules.catalog.models import Product
from app.modules.lab.reset import _wipe, add_history, make_user
from app.modules.auth.models import CUSTOMER
from app.modules.catalog import seed as catalog_seed
from app.modules.promotion import seed as promotion_seed
from app.modules.risk.models import DecisionPolicy, Rule, RuleVersion
from app.modules.risk.seed import seed_rules
from app.modules.simulation.models import SimLabel, SimRun
from simulator.personas import Account, Group, build_population

PASSWORD = "sim-matkhau-123"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Khoảng tin cậy Wilson 95% cho tỷ lệ k/n (ổn định hơn công thức chuẩn khi n nhỏ hoặc tỷ lệ gần 0/1)."""
    if n == 0:
        return None
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)


def _pct(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    return round(s[max(0, math.ceil(p / 100 * len(s)) - 1)], 2)


class Actions:
    """Các thao tác của một người dùng mô phỏng, gọi qua API thật."""

    def __init__(self, db: Session, skus: dict[str, Product]):
        self.db = db
        self.skus = skus
        self.request_ms: dict[str, list[float]] = defaultdict(list)
        self.errors: list[str] = []

    def _client(self, a: Account) -> TestClient:
        c = TestClient(app, client=(a.ip, 50000))
        c.headers["X-Device-Id"] = a.device
        return c

    def _timed(self, kind: str, fn: Callable):
        started = time.perf_counter()
        r = fn()
        self.request_ms[kind].append((time.perf_counter() - started) * 1000)
        if r.status_code >= 500:
            self.errors.append(f"{kind}: {r.status_code} {r.text[:200]}")
        return r

    def register(self, a: Account) -> None:
        a.client = self._client(a)
        r = a.client.post("/api/auth/register",
                          json={"email": f"{a.key}@sim.test", "password": PASSWORD, "full_name": a.key})
        a.user_id = r.json()["id"]

    def login(self, a: Account) -> None:
        a.client = self._client(a)
        r = a.client.post("/api/auth/login", json={"email": f"{a.key}@sim.test", "password": PASSWORD})
        a.user_id = r.json()["id"]

    def view(self, a: Account, sku: str) -> None:
        a.client.get(f"/api/products/{self.skus[sku].slug}")

    def add(self, a: Account, sku: str, qty: int) -> None:
        a.client.post("/api/cart/items", json={"product_id": self.skus[sku].id, "quantity": qty})

    def voucher(self, a: Account, code: str) -> None:
        self._timed("voucher_apply", lambda: a.client.post("/api/cart/voucher", json={"code": code}))

    def checkout(self, a: Account, address: dict, cod: bool, abandon_if_no_cod: bool) -> None:
        if cod:
            opts = self._timed("payment_options", lambda: a.client.get("/api/orders/payment-options")).json()
            if not opts.get("cod_allowed", True):
                if abandon_if_no_cod:
                    return  # kẻ bùng hàng không chịu trả trước: bỏ đơn
                cod = False
        r = self._place(a, address, "COD" if cod else "PREPAID")
        if r.status_code == 409 and r.json()["error"]["code"] == "COD_NOT_AVAILABLE" and not abandon_if_no_cod:
            self._place(a, address, "PREPAID")
        elif r.status_code == 409 and r.json()["error"]["code"] == "VOUCHER_NOT_APPLICABLE":
            self._place(a, address, "COD" if cod else "PREPAID")  # khách hợp lệ mua tiếp với giá gốc

    def checkout_if_voucher(self, a: Account, address: dict) -> None:
        """Farm chỉ mua khi còn voucher; bị gỡ voucher thì bỏ."""
        if a.client.get("/api/cart").json().get("voucher"):
            self._place(a, address, "PREPAID")

    def _place(self, a: Account, address: dict, method: str):
        return self._timed("place_order", lambda: a.client.post(
            "/api/orders/checkout", json={"address": address, "payment_method": method},
            headers={"Idempotency-Key": str(uuid.uuid4())}))


def _rules_fingerprint(db: Session) -> str:
    rows = db.execute(select(Rule.code, RuleVersion.version, RuleVersion.params, RuleVersion.enabled)
                      .join(RuleVersion, RuleVersion.id == Rule.active_version_id).order_by(Rule.code)).all()
    pols = db.execute(select(DecisionPolicy.context, DecisionPolicy.thresholds)
                      .where(DecisionPolicy.is_active.is_(True)).order_by(DecisionPolicy.context)).all()
    blob = json.dumps([[list(map(str, r)) for r in rows], [list(map(str, p)) for p in pols]], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _prepare(db: Session) -> dict[str, Product]:
    _wipe(db)
    catalog_seed.seed(db)
    promotion_seed.seed(db)
    seed_rules(db)
    db.execute(text("UPDATE products SET stock = 100000"))  # mô phỏng không đo chuyện hết hàng
    db.commit()
    return {p.sku: p for p in db.scalars(select(Product))}


def run(session_factory: Callable[[], Session], dataset: str, seed: int, scale: float = 1.0,
        progress: Callable[[str], None] = print) -> dict:
    rng = random.Random(seed)
    db = session_factory()
    skus = _prepare(db)

    def _get_db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _get_db
    try:
        actions = Actions(db, skus)
        groups = build_population(dataset, rng, scale, actions)
        accounts = [a for g in groups for a in g.accounts]

        # Lịch sử quá khứ: tạo tài khoản cũ và đơn đã kết thúc (dữ liệu seed)
        cheap = skus["SM-002"]
        for a in accounts:
            if a.age_days is not None:
                u = make_user(db, f"{a.key}@sim.test", a.key, CUSTOMER, PASSWORD, timedelta(days=a.age_days))
                if a.history:
                    add_history(db, u, cheap, a.history)
        db.commit()

        sim_run = SimRun(dataset=dataset, seed=seed, rules_fingerprint=_rules_fingerprint(db),
                         config={"scale": scale, "groups": len(groups), "accounts": len(accounts)})
        db.add(sim_run)
        db.commit()
        progress(f"Dân số: {len(accounts)} tài khoản trong {len(groups)} nhóm. Đang chạy hành vi…")

        # Trộn bước giữa các nhóm: mỗi lượt chọn ngẫu nhiên một nhóm còn bước để chạy bước kế tiếp
        started = time.perf_counter()
        pending = [list(g.steps) for g in groups]
        total = sum(len(p) for p in pending)
        done = 0
        while pending:
            i = rng.randrange(len(pending))
            pending[i].pop(0)()
            done += 1
            if not pending[i]:
                pending.pop(i)
            if done % 300 == 0:
                progress(f"  {done}/{total} bước")
        elapsed = time.perf_counter() - started

        for a in accounts:
            db.add(SimLabel(run_id=sim_run.id, user_id=a.user_id, persona=a.persona, group_id=a.group,
                            is_abuse=a.is_abuse, hard_negative=a.hard_negative, unseen_variant=a.unseen))
        db.commit()

        metrics = evaluate(db, sim_run.id)
        metrics["runtime"] = {"seconds": round(elapsed, 1), "steps": total, "server_errors": actions.errors[:10]}
        metrics["request_ms"] = {k: {"n": len(v), "p50": _pct(v, 50), "p95": _pct(v, 95), "p99": _pct(v, 99)}
                                 for k, v in actions.request_ms.items()}
        sim_run.metrics = metrics
        sim_run.finished_at = utcnow()
        db.commit()
        return {"run_id": sim_run.id, "dataset": dataset, "seed": seed, "scale": scale,
                "rules_fingerprint": sim_run.rules_fingerprint, **metrics}
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        db.close()


def evaluate(db: Session, run_id: int) -> dict:
    """So quyết định của hệ thống với nhãn thật. Chỉ bộ đánh giá đọc sim_labels."""
    rows = db.execute(text("""
        SELECT l.user_id, l.persona, l.group_id, l.is_abuse, l.hard_negative, l.unseen_variant,
               COALESCE(MAX(d.decision <> 'ALLOW'), 0) AS flagged
        FROM sim_labels l LEFT JOIN risk_decisions d ON d.user_id = l.user_id
        WHERE l.run_id = :run GROUP BY l.user_id, l.persona, l.group_id, l.is_abuse, l.hard_negative, l.unseen_variant
    """), {"run": run_id}).all()

    tp = sum(1 for r in rows if r.is_abuse and r.flagged)
    fn = sum(1 for r in rows if r.is_abuse and not r.flagged)
    fp = sum(1 for r in rows if not r.is_abuse and r.flagged)
    tn = sum(1 for r in rows if not r.is_abuse and not r.flagged)

    def rate(k, n):
        return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "ci95": wilson(k, n)}

    per_persona = defaultdict(lambda: {"n": 0, "flagged": 0, "is_abuse": False, "hard_negative": False, "unseen": False})
    for r in rows:
        p = per_persona[r.persona]
        p["n"] += 1
        p["flagged"] += int(r.flagged)
        p["is_abuse"], p["hard_negative"], p["unseen"] = bool(r.is_abuse), bool(r.hard_negative), bool(r.unseen_variant)

    # Theo nhóm: một farm bị "phát hiện" nếu ít nhất một tài khoản của nó bị gắn cờ
    groups = defaultdict(list)
    for r in rows:
        if r.is_abuse:
            groups[(r.persona, r.group_id)].append(bool(r.flagged))
    group_recall = defaultdict(lambda: [0, 0])
    for (persona, _), flags in groups.items():
        group_recall[persona][0] += int(any(flags))
        group_recall[persona][1] += 1

    hard = [r for r in rows if r.hard_negative]
    normal_legit = [r for r in rows if not r.is_abuse and not r.hard_negative]
    unseen = [r for r in rows if r.unseen_variant]
    seen_abuse = [r for r in rows if r.is_abuse and not r.unseen_variant]

    # Tác động nghiệp vụ trong lần chạy
    vouchers = db.execute(text("""
        SELECT l.is_abuse, COUNT(*) FROM voucher_redemptions v JOIN sim_labels l ON l.user_id = v.user_id
        WHERE l.run_id = :run GROUP BY l.is_abuse"""), {"run": run_id}).all()
    cod_orders = db.execute(text("""
        SELECT l.persona, o.status, COUNT(*) FROM orders o JOIN sim_labels l ON l.user_id = o.user_id
        WHERE l.run_id = :run AND o.payment_method = 'COD' AND o.order_code NOT LIKE 'RSSEED%%'
        GROUP BY l.persona, o.status"""), {"run": run_id}).all()
    latency = [float(x[0]) for x in db.execute(text("""
        SELECT d.latency_ms FROM risk_decisions d JOIN sim_labels l ON l.user_id = d.user_id
        WHERE l.run_id = :run AND d.error IS NULL"""), {"run": run_id}).all()]

    return {
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "precision": rate(tp, tp + fp),
        "recall": rate(tp, tp + fn),
        "fpr": rate(fp, fp + tn),
        "fpr_normal": rate(sum(1 for r in normal_legit if r.flagged), len(normal_legit)),
        "fpr_hard_negative": rate(sum(1 for r in hard if r.flagged), len(hard)),
        "recall_seen_variants": rate(sum(1 for r in seen_abuse if r.flagged), len(seen_abuse)),
        "recall_unseen_variants": rate(sum(1 for r in unseen if r.flagged), len(unseen)),
        "per_persona": {k: {**v, "rate": round(v["flagged"] / v["n"], 4)} for k, v in sorted(per_persona.items())},
        "group_recall": {k: {"caught": c, "groups": n} for k, (c, n) in group_recall.items()},
        "business": {
            "vouchers_redeemed_by_abuse": next((c for a, c in vouchers if a), 0),
            "vouchers_redeemed_by_legit": next((c for a, c in vouchers if not a), 0),
            "cod_orders_by_persona": {f"{p}:{s}": c for p, s, c in cod_orders},
        },
        "risk_latency_ms": {"n": len(latency), "p50": _pct(latency, 50), "p95": _pct(latency, 95),
                            "p99": _pct(latency, 99)},
    }
