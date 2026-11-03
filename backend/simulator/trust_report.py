"""Phân bố điểm tin cậy theo nhóm persona của lần mô phỏng gần nhất (đọc CSDL mô phỏng, chỉ đọc).

Chạy ngay sau `python -m simulator ...` (lần chạy sau sẽ xóa dữ liệu):
    .venv/Scripts/python -m simulator.trust_report --out ../docs/experiments/<tên>.json

Mỗi tài khoản lấy điểm tin cậy THẤP NHẤT qua mọi quyết định. "Bị hạn chế" = có ít nhất một quyết định khác ALLOW
(cùng định nghĩa "bị gắn cờ" của bộ đánh giá).
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import make_engine
from app.modules.risk.models import RiskDecision
from app.modules.simulation.models import SimLabel


def distribution(db: Session) -> dict:
    labels = {l.user_id: l for l in db.scalars(select(SimLabel))}
    min_trust: dict[int, int] = {}
    restricted: set[int] = set()
    case: set[int] = set()
    for user_id, decision, actions, snap in db.execute(
            select(RiskDecision.user_id, RiskDecision.decision, RiskDecision.actions, RiskDecision.features_snapshot)):
        if user_id not in labels:
            continue
        t = (snap or {}).get("trust_score")
        if t is not None:
            min_trust[user_id] = min(t, min_trust.get(user_id, t))
        if decision != "ALLOW":
            restricted.add(user_id)
        if (actions or {}).get("open_case"):
            case.add(user_id)

    groups: dict[str, list[int]] = defaultdict(list)
    for uid, label in labels.items():
        groups[label.persona].append(uid)
    out = {}
    for persona, uids in sorted(groups.items()):
        scores = [min_trust[u] for u in uids if u in min_trust]
        out[persona] = {
            "n": len(uids),
            "abuse": labels[uids[0]].is_abuse,
            "restricted": sum(u in restricted for u in uids),
            "trust<50": sum(s < 50 for s in scores),
            "trust<30": sum(s < 30 for s in scores),
            "open_case": sum(u in case for u in uids),
            "trust_median": statistics.median(scores) if scores else None,
        }
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    with Session(make_engine(get_settings().sim_database_url)) as db:
        result = distribution(db)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
