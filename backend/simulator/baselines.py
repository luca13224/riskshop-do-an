"""Baseline: các cách "ngây thơ" để so với Risk Engine trên CÙNG một lần chạy mô phỏng.

Câu hỏi hội đồng sẽ hỏi: "Risk Engine tốt hơn cái gì?". Nên đo thêm 3 mốc:

- B0 · Không kiểm soát: không gắn cờ ai. Recall = 0, nhưng accuracy vẫn cao vì đa số khách là hợp lệ,
  nên đây là ví dụ cho thấy accuracy dễ đánh lừa khi dữ liệu lệch lớp.
- B1 · Luật thủ công: 2 luật cứng một shop nhỏ hay tự đặt. Chốt TRƯỚC khi chạy, không tinh chỉnh theo kết quả:
    (a) dùng mã người mới trên thiết bị đã có từ 2 tài khoản mới trong 30 ngày;
    (b) đặt COD khi đã từng có đơn COD giao thất bại.
- B2 · Ngẫu nhiên: gắn cờ ngẫu nhiên đúng bằng tỷ lệ Risk Engine gắn cờ. Tính theo kỳ vọng
  (precision = tỷ lệ kẻ lạm dụng, recall = FPR = tỷ lệ gắn cờ), không cần bốc thăm.

Cách chấm B1 (phát lại, "shadow"): áp luật lên đúng ảnh chụp đặc trưng (features_snapshot) mà Risk Engine
đã thấy ở từng lần chấm điểm, rồi gộp theo tài khoản như Risk Engine (gắn cờ nếu có ít nhất một lần).
Giới hạn: hành trình là hành trình khi có Risk Engine (kẻ bị gỡ mã có thể bỏ đơn sớm), nên B1 chỉ thấy
những điểm chấm mà hành trình đó đi qua.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.orm import Session


def manual_rules(features: dict) -> bool:
    """B1. Trả True nếu luật thủ công gắn cờ lần chấm điểm này."""
    shared_device = bool(features.get("voucher_new_user")) and (features.get("new_accounts_on_device_30d") or 0) >= 2
    cod_bad_history = bool(features.get("payment_cod")) and (features.get("cod_failed") or 0) >= 1
    return shared_device or cod_bad_history


def scores(tp: int, fp: int, tn: int, fn: int) -> dict:
    """Bộ chỉ số dùng chung cho Risk Engine và mọi baseline."""
    n = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None
    return {
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "precision": _r(precision),
        "recall": _r(recall),
        "f1": _r(f1),
        "fpr": _r(fp / (fp + tn) if fp + tn else None),
        "accuracy": _r((tp + tn) / n if n else None),
    }


def _r(x: float | None) -> float | None:
    return None if x is None else round(x, 4)


def _confusion(labels: dict[int, bool], flagged: set[int]) -> tuple[int, int, int, int]:
    tp = sum(1 for u, abuse in labels.items() if abuse and u in flagged)
    fp = sum(1 for u, abuse in labels.items() if not abuse and u in flagged)
    tn = sum(1 for u, abuse in labels.items() if not abuse and u not in flagged)
    fn = sum(1 for u, abuse in labels.items() if abuse and u not in flagged)
    return tp, fp, tn, fn


def evaluate_baselines(db: Session, run_id: int, engine_flagged: set[int]) -> dict:
    rows = db.execute(text("SELECT user_id, is_abuse, persona FROM sim_labels WHERE run_id = :run"), {"run": run_id}).all()
    labels = {int(u): bool(a) for u, a, _ in rows}
    persona_of = {int(u): p for u, _, p in rows}
    snapshots = defaultdict(list)
    for user_id, snap in db.execute(text("""
        SELECT d.user_id, d.features_snapshot FROM risk_decisions d
        JOIN sim_labels l ON l.user_id = d.user_id WHERE l.run_id = :run AND d.error IS NULL"""),
            {"run": run_id}).all():
        snapshots[int(user_id)].append(snap if isinstance(snap, dict) else _json(snap))

    manual = {u for u, snaps in snapshots.items() if any(manual_rules(s) for s in snaps)}
    n = len(labels)
    abuse_rate = sum(labels.values()) / n if n else 0.0
    flag_rate = len(engine_flagged & labels.keys()) / n if n else 0.0
    pos, neg = sum(labels.values()), n - sum(labels.values())
    # Ngẫu nhiên theo kỳ vọng: số kỳ vọng ở từng ô của ma trận nhầm lẫn
    e_tp, e_fp = pos * flag_rate, neg * flag_rate
    random_expected = {
        "confusion": {"TP": round(e_tp, 1), "FP": round(e_fp, 1), "TN": round(neg - e_fp, 1), "FN": round(pos - e_tp, 1)},
        "precision": _r(abuse_rate if flag_rate else None),
        "recall": _r(flag_rate),
        "f1": _r(2 * e_tp / (2 * e_tp + e_fp + (pos - e_tp)) if pos else None),
        "fpr": _r(flag_rate),
        "accuracy": _r((e_tp + neg - e_fp) / n if n else None),
    }
    return {
        "engine": scores(*_confusion(labels, engine_flagged)),
        "no_control": scores(*_confusion(labels, set())),
        "manual_rules": scores(*_confusion(labels, manual)),
        "random_same_rate": random_expected,
        # B1 gắn cờ bao nhiêu tài khoản ở từng persona: để giải thích FP của luật thủ công rơi vào ai
        "manual_by_persona": {p: sum(1 for u in manual if persona_of.get(u) == p)
                              for p in sorted(set(persona_of.values()))},
        "abuse_rate": _r(abuse_rate),
        "engine_flag_rate": _r(flag_rate),
    }


def _json(raw) -> dict:
    import json
    return json.loads(raw) if raw else {}
