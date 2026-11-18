"""Báo tình trạng dữ liệu demo (chỉ đọc), dùng cho scripts/check.ps1 và scripts/prepare_demo.ps1.

    .venv/Scripts/python scripts/demo_status.py

In một dòng JSON: CSDL kết nối được không, DEMO_MODE, số lượt chấm điểm trong 24 giờ / 7 ngày,
lần chấm gần nhất cách đây bao nhiêu giờ, tài khoản demo có đủ không, số việc nền đang chờ.
Dữ liệu lịch sử demo tính lùi từ ngày tạo, nên sau khoảng một tuần các trang Tổng quan / Báo cáo
sẽ trống dần: khi đó chạy lại scripts/prepare_demo.bat.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import bindparam, text  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import engine  # noqa: E402

DEMO_ACCOUNTS = ["admin1@test.com", "admin2@test.com", "admin3@test.com",
                 "user1@test.com", "user2@test.com", "user3@test.com"]


def main() -> int:
    out: dict = {"demo_mode": get_settings().demo_mode}
    try:
        with engine.connect() as c:
            row = c.execute(text("""
                SELECT SUM(created_at >= UTC_TIMESTAMP() - INTERVAL 1 DAY),
                       SUM(created_at >= UTC_TIMESTAMP() - INTERVAL 7 DAY),
                       TIMESTAMPDIFF(HOUR, MAX(created_at), UTC_TIMESTAMP())
                FROM risk_decisions""")).one()
            out["decisions_24h"] = int(row[0] or 0)
            out["decisions_7d"] = int(row[1] or 0)
            out["hours_since_last"] = None if row[2] is None else int(row[2])
            q = text("SELECT email FROM users WHERE email IN :e").bindparams(bindparam("e", expanding=True))
            found = {r[0] for r in c.execute(q, {"e": DEMO_ACCOUNTS})}
            out["missing_accounts"] = [e for e in DEMO_ACCOUNTS if e not in found]
            out["jobs_queued"] = int(c.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'queued'")).scalar() or 0)
            out["active_restrictions"] = int(c.execute(text(
                "SELECT COUNT(*) FROM account_restrictions WHERE lifted_at IS NULL "
                "AND (expires_at IS NULL OR expires_at > UTC_TIMESTAMP())")).scalar() or 0)
        out["db"] = "ok"
    except Exception as exc:  # noqa: BLE001 - báo lỗi gọn cho người vận hành, không in traceback
        out["db"] = f"lỗi: {type(exc).__name__}"
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["db"] == "ok" else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
