"""Kiểm tra bộ mô phỏng: chạy quy mô nhỏ trên CSDL test, chỉ số phải nhất quán và tái lập được theo seed."""

import random

from conftest import TestSession
from simulator.baselines import manual_rules, scores
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
    # Baseline chấm trên cùng tài khoản: tổng ma trận nhầm lẫn khớp; B0 không bắt được ai
    b = m["baselines"]
    assert b["engine"]["confusion"] == c and b["engine"]["f1"] == m["f1"]
    assert b["no_control"]["recall"] == 0 and b["no_control"]["fpr"] == 0
    assert sum(b["manual_rules"]["confusion"].values()) == sum(c.values())
    assert "So với baseline" in render_markdown(m)


def test_scores_and_manual_rules():
    s = scores(tp=8, fp=2, tn=88, fn=2)
    assert s["precision"] == 0.8 and s["recall"] == 0.8 and s["f1"] == 0.8 and s["accuracy"] == 0.96
    # Không gắn cờ ai: accuracy vẫn 90% dù không bắt được kẻ lạm dụng nào
    assert scores(tp=0, fp=0, tn=90, fn=10)["accuracy"] == 0.9
    assert manual_rules({"voucher_new_user": True, "new_accounts_on_device_30d": 2})
    assert not manual_rules({"voucher_new_user": True, "new_accounts_on_device_30d": 1})
    assert manual_rules({"payment_cod": True, "cod_failed": 1})
    assert not manual_rules({"payment_cod": False, "cod_failed": 3})


def test_ban_evaders_are_locked_but_relatives_are_not():
    """Bộ dev_v3 (mục tiêu O7): tài khoản né lệnh khóa đều bị gắn cờ và không lấy được mã; người nhà không bị khóa.
    (Kẻ né khóa bỏ đơn ngay khi bị gỡ mã thì chưa bị ghi lệnh khóa: xem TEST_PLAN 3h.)"""
    m = run(TestSession, "dev_v3", seed=3, scale=0.4)
    assert m["runtime"]["server_errors"] == []
    evader, relative = m["per_persona"]["ban_evader"], m["per_persona"]["banned_relative"]
    assert evader["flagged"] == evader["n"] and evader.get("vouchers", 0) == 0
    assert "purchase_linked" not in relative.get("locked", {})
