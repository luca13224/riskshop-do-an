"""Chạy mô phỏng và ghi báo cáo thực nghiệm.

    .venv/Scripts/python -m simulator --dataset dev --seed 1
    .venv/Scripts/python -m simulator --dataset test --seed 2 --confirm-test

Quy tắc chống "học thuộc" (bản tư vấn mục 7.3):
- Tinh chỉnh luật CHỈ dựa trên tập dev, chạy bao nhiêu lần cũng được.
- Tập test chỉ chạy SAU KHI đã khóa luật, và chỉ chạy một lần cho mỗi phiên bản luật
  (báo cáo ghi dấu vân tay của bộ luật để kiểm chứng điều này).
"""

import argparse
import logging
import json
import sys
from pathlib import Path

from sqlalchemy.orm import sessionmaker

from app.core.config import BACKEND_DIR, get_settings
from app.core.db import make_engine
from simulator.personas import DATASETS
from simulator.report import render_markdown
from simulator.runner import run

REPORT_DIR = BACKEND_DIR.parent / "docs" / "experiments"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # bỏ log từng request
    parser = argparse.ArgumentParser(description="Bộ mô phỏng đánh giá Risk Engine")
    parser.add_argument("--dataset", choices=sorted(DATASETS), default="dev")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--scale", type=float, default=1.0, help="nhân số lượng persona (ví dụ 0.3 để chạy nhanh)")
    parser.add_argument("--confirm-test", action="store_true", help="xác nhận đã khóa luật trước khi chạy tập test")
    parser.add_argument("--disable-rule", action="append", default=[], metavar="CODE",
                        help="tắt một luật theo mã (lặp lại được), ví dụ để chạy bộ luật v1 trên tập test_v2")
    parser.add_argument("--no-trust", action="store_true",
                        help="tắt lớp điểm tin cậy (bậc Trust và min_trust của mã), để so với bộ luật v3")
    args = parser.parse_args()

    url = get_settings().sim_database_url
    if not url or "sim" not in url:
        print("Thiếu SIM_DATABASE_URL (phải trỏ tới CSDL riêng có chữ 'sim', vì mô phỏng sẽ XÓA dữ liệu).",
              file=sys.stderr)
        return 1
    if args.dataset.startswith("test") and not args.confirm_test:
        print("Tập test chỉ chạy sau khi đã khóa luật. Chạy lại kèm --confirm-test nếu chắc chắn.", file=sys.stderr)
        return 1

    session_factory = sessionmaker(bind=make_engine(url), autoflush=False, expire_on_commit=False)
    result = run(session_factory, args.dataset, args.seed, args.scale, disable_rules=tuple(args.disable_rule),
                 no_trust=args.no_trust)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{args.dataset}_seed{args.seed}_scale{args.scale:g}"
    if args.disable_rule:
        stem += "_without-" + "-".join(sorted(args.disable_rule))
    if args.no_trust:
        stem += "_no-trust"
    (REPORT_DIR / f"{stem}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str),
                                             encoding="utf-8")
    (REPORT_DIR / f"{stem}.md").write_text(render_markdown(result), encoding="utf-8")
    m = result
    print(f"Precision {m['precision']['value']} · Recall {m['recall']['value']} · FPR {m['fpr']['value']}")
    print(f"Báo cáo: docs/experiments/{stem}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
