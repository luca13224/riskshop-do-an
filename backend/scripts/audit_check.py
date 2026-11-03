"""Kiểm tra tính giải thích được và truy vết (kịch bản E3, mục tiêu O6 / NFR-02, NFR-03). CHỈ ĐỌC.

    .venv/Scripts/python scripts/audit_check.py            # CSDL chính (dữ liệu demo)
    .venv/Scripts/python scripts/audit_check.py --sim      # CSDL mô phỏng (lần chạy simulator gần nhất)
    ... --out ../docs/experiments/audit_check_<tên>.json

Mỗi mục kiểm tra trả về: tổng số bản ghi, số bản ghi vi phạm, và tối đa 5 id vi phạm để tra lại.
Quyết định khác ALLOW không có luật khớp vẫn được coi là có lý do nếu lý do nằm ở chỗ khác đã lưu cùng quyết định:
sổ trừ điểm tin cậy (trust_deductions trong ảnh chụp đặc trưng), lệnh khóa tài khoản đang hiệu lực, hoặc lỗi Risk Engine (cột error).
"""

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

CHECKS = {
    "decision_not_allow_has_reason": (
        "Quyết định khác ALLOW có lý do (luật khớp / bậc tin cậy / lệnh khóa / lỗi có ghi)",
        "SELECT COUNT(*) FROM risk_decisions WHERE decision <> 'ALLOW'",
        """SELECT d.id FROM risk_decisions d
           WHERE d.decision <> 'ALLOW'
             AND NOT EXISTS (SELECT 1 FROM rule_hits h WHERE h.decision_id = d.id)
             AND COALESCE(JSON_LENGTH(d.features_snapshot, '$.trust_deductions'), 0) = 0
             AND NOT EXISTS (SELECT 1 FROM account_restrictions r WHERE r.decision_id = d.id
                             OR (r.user_id = d.user_id AND r.created_at <= d.created_at))
             AND d.error IS NULL"""),
    "decision_has_snapshot_and_policy": (
        "Mọi quyết định có ảnh chụp đặc trưng và phiên bản ma trận (trừ khi lỗi có ghi, hoặc bị chặn vì đang khóa)",
        "SELECT COUNT(*) FROM risk_decisions",
        """SELECT id FROM risk_decisions
           WHERE error IS NULL AND (features_snapshot IS NULL OR JSON_LENGTH(features_snapshot) = 0
                                    OR policy_id IS NULL)
             -- Đang bị khóa thì không chấm điểm (ADR-010): lý do là lệnh khóa, lưu trong ảnh chụp
             AND JSON_EXTRACT(features_snapshot, '$.account_restriction') IS NULL"""),
    "rule_hit_complete": (
        "Mọi luật khớp có câu lý do, giá trị thực tế, trỏ đúng phiên bản luật",
        "SELECT COUNT(*) FROM rule_hits",
        """SELECT h.id FROM rule_hits h LEFT JOIN rule_versions v ON v.id = h.rule_version_id
           WHERE v.id IS NULL OR h.reason_text = '' OR h.observed IS NULL OR JSON_LENGTH(h.observed) = 0"""),
    "case_closed_has_reason_and_audit": (
        "Case đã đóng có lý do kết luận và bản ghi audit case.resolve",
        "SELECT COUNT(*) FROM risk_cases WHERE closed_at IS NOT NULL",
        """SELECT c.id FROM risk_cases c WHERE c.closed_at IS NOT NULL
             AND (COALESCE(c.outcome_reason, '') = ''
                  OR NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.action = 'case.resolve'
                                 AND a.entity_type = 'case' AND a.entity_id = c.case_code))"""),
    "appeal_resolved_has_response_and_audit": (
        "Khiếu nại đã kết luận có câu trả lời cho khách và bản ghi audit appeal.resolve",
        "SELECT COUNT(*) FROM appeals WHERE resolved_at IS NOT NULL",
        """SELECT p.id FROM appeals p WHERE p.resolved_at IS NOT NULL
             AND (COALESCE(p.response, '') = ''
                  OR NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.action = 'appeal.resolve'
                                 AND a.entity_type = 'appeal' AND a.entity_id = p.appeal_code))"""),
    "restriction_has_audit": (
        "Mọi lệnh khóa có audit (account.restrict tự động / account.ban của nhân viên)",
        "SELECT COUNT(*) FROM account_restrictions",
        """SELECT r.id FROM account_restrictions r
           WHERE NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.entity_type = 'user'
                             AND a.entity_id = CAST(r.user_id AS CHAR) COLLATE utf8mb4_unicode_ci
                             AND a.action = IF(r.source = 'staff', 'account.ban', 'account.restrict') COLLATE utf8mb4_unicode_ci)"""),
    "restriction_lift_has_reason_and_audit": (
        "Lệnh khóa đã gỡ có người gỡ, lý do và audit account.unrestrict (hoặc gỡ qua khiếu nại)",
        "SELECT COUNT(*) FROM account_restrictions WHERE lifted_at IS NOT NULL",
        """SELECT r.id FROM account_restrictions r WHERE r.lifted_at IS NOT NULL
             AND (COALESCE(r.lift_reason, '') = ''
                  OR NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.entity_type = 'user'
                                 AND a.entity_id = CAST(r.user_id AS CHAR) COLLATE utf8mb4_unicode_ci
                                 AND a.action IN ('account.unrestrict', 'appeal.resolve')))"""),
    "rule_change_has_audit": (
        "Phiên bản luật do nhân viên tạo có audit rule.new_version",
        "SELECT COUNT(*) FROM rule_versions WHERE created_by IS NOT NULL",
        """SELECT v.id FROM rule_versions v JOIN rules r ON r.id = v.rule_id
           WHERE v.created_by IS NOT NULL
             AND NOT EXISTS (SELECT 1 FROM audit_logs a WHERE a.action = 'rule.new_version'
                             AND a.entity_type = 'rule' AND a.entity_id = r.code)"""),
}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Kiểm tra giải thích được và audit (chỉ đọc)")
    parser.add_argument("--sim", action="store_true", help="dùng CSDL mô phỏng thay vì CSDL chính")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    from app.core.config import get_settings
    s = get_settings()
    url = s.sim_database_url if args.sim else s.database_url
    report = {"database": "sim" if args.sim else "main", "checks": {}}
    with create_engine(url).connect() as conn:
        for key, (label, total_sql, bad_sql) in CHECKS.items():
            total = conn.execute(text(total_sql)).scalar_one()
            bad = [row[0] for row in conn.execute(text(bad_sql))]
            report["checks"][key] = {"label": label, "total": total, "violations": len(bad), "examples": bad[:5],
                                     "pass_rate": None if total == 0 else round(1 - len(bad) / total, 4)}
            mark = "OK " if not bad else "LỖI"
            print(f"[{mark}] {label}: {total - len(bad)}/{total}" + (f" · ví dụ id {bad[:5]}" if bad else ""))
    if args.out:
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all(c["violations"] == 0 for c in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
