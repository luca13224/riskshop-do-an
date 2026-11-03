"""Kiểm tra bộ mô phỏng: chạy quy mô nhỏ trên CSDL test, chỉ số phải nhất quán và tái lập được theo seed."""

import random

from conftest import TestSession
from simulator.personas import build_population
from simulator.report import render_markdown
from simulator.runner import run, wilson


def test_wilson_interval():
    assert wilson(0, 0) is None
    lo, hi = wilson(5, 10)
    assert 0.18 < lo < 0.24 and 0.76 < hi < 0.82
    lo, hi = wilson(0, 20)
    assert lo == 0 and hi < 0.2


def test_population_is_deterministic_by_seed():
    a = build_population("dev", random.Random(7), 0.2, actions=None)
    b = build_population("dev", random.Random(7), 0.2, actions=None)
    keys = lambda groups: [(acc.persona, acc.device, acc.ip) for g in groups for acc in g.accounts]
    assert keys(a) == keys(b)


def test_small_run_metrics_are_consistent():
    m = run(TestSession, "dev", seed=3, scale=0.15)
    c = m["confusion"]
    assert m["runtime"]["server_errors"] == []
    assert c["TP"] + c["FN"] == sum(p["n"] for p in m["per_persona"].values() if p["is_abuse"])
    assert c["FP"] + c["TN"] == sum(p["n"] for p in m["per_persona"].values() if not p["is_abuse"])
    # Khách hợp lệ thông thường (không phải hard negative) không bị gắn cờ trong kịch bản chuẩn
    assert m["fpr_normal"]["k"] == 0
    assert "Toàn bộ dữ liệu là mô phỏng" in render_markdown(m)


def test_ban_evaders_are_locked_but_relatives_are_not():
    """Bộ dev_v3 (mục tiêu O7): tài khoản né lệnh khóa đều bị gắn cờ và không lấy được mã; người nhà không bị khóa.
    (Kẻ né khóa bỏ đơn ngay khi bị gỡ mã thì chưa bị ghi lệnh khóa: xem TEST_PLAN 3h.)"""
    m = run(TestSession, "dev_v3", seed=3, scale=0.4)
    assert m["runtime"]["server_errors"] == []
    evader, relative = m["per_persona"]["ban_evader"], m["per_persona"]["banned_relative"]
    assert evader["flagged"] == evader["n"]
    assert "purchase_linked" not in relative.get("locked", {})
