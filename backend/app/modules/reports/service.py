"""Báo cáo KPI (cảnh 7 của kịch bản demo). Chỉ đọc; đọc nhiều bảng nên dùng SQL thuần như feature store.

Các con số "tác động nghiệp vụ" là ƯỚC TÍNH dựa trên giả định ghi rõ trong ASSUMPTIONS,
và chỉ phản ánh dữ liệu trong hệ thống (kể cả dữ liệu do Attack Lab tạo ra).
"""

import math
from datetime import timedelta

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.privacy import mask_email
from app.core.time import utcnow

# Giả định để quy đổi ra tiền. Ghi rõ trong báo cáo, không phải số liệu thật của sàn nào.
COD_FAILED_COST = 30_000  # chi phí giao + hoàn một đơn COD thất bại (VND)

ASSUMPTIONS = [
    "Giá trị voucher ngăn được = tổng mức giảm của voucher bị gỡ, mỗi tài khoản và mỗi mã tính một lần.",
    f"Mỗi đơn COD rủi ro bị chuyển sang trả trước hoặc bị từ chối sau xác minh tránh được {COD_FAILED_COST:,}đ"
    " chi phí giao và hoàn hàng.".replace(",", "."),
    "Tỷ lệ chính xác của luật = số case kết luận lạm dụng / số case đã kết luận có luật đó khớp.",
    "Số liệu bao gồm cả dữ liệu mô phỏng từ Attack Lab.",
]


def _percentile(sorted_values: list[float], p: float) -> float | None:
    """Phân vị theo phương pháp nearest-rank."""
    if not sorted_values:
        return None
    k = max(0, math.ceil(p / 100 * len(sorted_values)) - 1)
    return round(sorted_values[k], 2)


def kpi(db: Session, days: int) -> dict:
    since = utcnow() - timedelta(days=days)
    params = {"since": since}

    def rows(sql: str, **extra):
        return db.execute(text(sql), {**params, **extra}).all()

    by_decision = dict(rows("SELECT decision, COUNT(*) FROM risk_decisions WHERE created_at >= :since GROUP BY decision"))
    by_context = dict(rows("SELECT context, COUNT(*) FROM risk_decisions WHERE created_at >= :since GROUP BY context"))
    latencies = sorted(
        float(r[0]) for r in rows("SELECT latency_ms FROM risk_decisions WHERE created_at >= :since AND error IS NULL")
    )
    errors = db.execute(
        text("SELECT COUNT(*) FROM risk_decisions WHERE created_at >= :since AND error IS NOT NULL"), params
    ).scalar()

    cases = dict(rows("SELECT status, COUNT(*) FROM risk_cases WHERE opened_at >= :since GROUP BY status"))
    resolve_minutes = db.execute(
        text("""SELECT AVG(TIMESTAMPDIFF(SECOND, opened_at, closed_at)) / 60 FROM risk_cases
                WHERE opened_at >= :since AND closed_at IS NOT NULL"""), params
    ).scalar()

    # Voucher ngăn được: mỗi (tài khoản, mã) bị gỡ tính một lần, theo mức giảm cố định của mã
    voucher_saved = db.execute(text("""
        SELECT COALESCE(SUM(v.amount), 0), COUNT(*) FROM (
            SELECT DISTINCT d.user_id, JSON_UNQUOTE(JSON_EXTRACT(d.features_snapshot, '$.voucher_code')) AS code
            FROM risk_decisions d
            WHERE d.created_at >= :since AND JSON_EXTRACT(d.actions, '$.remove_voucher') = true
        ) x JOIN vouchers v ON v.code = x.code AND v.discount_type = 'fixed'
    """), params).one()

    cod_restricted_users = db.execute(text("""
        SELECT COUNT(DISTINCT user_id) FROM risk_decisions
        WHERE created_at >= :since AND context = 'place_order' AND JSON_EXTRACT(actions, '$.disable_cod') = true
    """), params).scalar()
    held = dict(rows("""
        SELECT o.status, COUNT(*) FROM risk_decisions d JOIN orders o ON o.id = d.order_id
        WHERE d.created_at >= :since AND d.decision = 'REVIEW' GROUP BY o.status
    """))
    rejected_after_review = held.get("REJECTED", 0)
    cleared_cases = cases.get("CLEARED", 0)

    # Hiệu quả từng luật: số lần khớp, và kết luận của các case có chứa quyết định mà luật đó khớp
    rule_rows = rows("""
        SELECT h.rule_code,
               COUNT(DISTINCT h.decision_id) AS hits,
               COUNT(DISTINCT CASE WHEN c.status = 'CONFIRMED_ABUSE' THEN c.id END) AS confirmed,
               COUNT(DISTINCT CASE WHEN c.status = 'CLEARED' THEN c.id END) AS cleared
        FROM rule_hits h
        JOIN risk_decisions d ON d.id = h.decision_id
        LEFT JOIN case_decisions cd ON cd.decision_id = d.id
        LEFT JOIN risk_cases c ON c.id = cd.case_id
        WHERE d.created_at >= :since
        GROUP BY h.rule_code ORDER BY hits DESC
    """)
    rule_names = dict(rows("SELECT code, name FROM rules"))

    return {
        "days": days,
        "decisions": {
            "total": sum(by_decision.values()),
            "by_decision": {k: by_decision.get(k, 0) for k in ("ALLOW", "ALLOW_WITH_RESTRICTION", "REVIEW", "BLOCK")},
            "by_context": by_context,
            "engine_errors": errors,
        },
        "latency_ms": {
            "samples": len(latencies),
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        },
        "cases": {
            "by_status": {k: cases.get(k, 0) for k in ("OPEN", "IN_REVIEW", "CONFIRMED_ABUSE", "CLEARED")},
            "avg_resolve_minutes": round(float(resolve_minutes), 1) if resolve_minutes is not None else None,
        },
        "impact": {
            "voucher_saved_vnd": int(voucher_saved[0]),
            "voucher_blocked_accounts": int(voucher_saved[1]),
            "cod_restricted_customers": int(cod_restricted_users),
            "orders_held": sum(held.values()),
            "orders_rejected_after_review": rejected_after_review,
            "cod_cost_avoided_vnd": (int(cod_restricted_users) + rejected_after_review) * COD_FAILED_COST,
            "legit_customers_held_by_mistake": cleared_cases,
        },
        "rules": [
            {
                "code": r.rule_code,
                "name": rule_names.get(r.rule_code, r.rule_code),
                "hits": r.hits,
                "cases_confirmed": r.confirmed,
                "cases_cleared": r.cleared,
                "precision": round(r.confirmed / (r.confirmed + r.cleared), 2) if (r.confirmed + r.cleared) else None,
            }
            for r in rule_rows
        ],
        "assumptions": ASSUMPTIONS,
    }


def audit_logs(db: Session, limit: int, entity_type: str | None) -> list[dict]:
    sql = """SELECT a.id, a.created_at, a.action, a.entity_type, a.entity_id, a.before_data, a.after_data, a.note,
                    u.full_name AS actor_name, u.role AS actor_role
             FROM audit_logs a LEFT JOIN users u ON u.id = a.actor_id"""
    params: dict = {"limit": limit}
    if entity_type:
        sql += " WHERE a.entity_type = :entity_type"
        params["entity_type"] = entity_type
    sql += " ORDER BY a.id DESC LIMIT :limit"
    return [dict(r._mapping) for r in db.execute(text(sql), params)]


# ---------------------------------------------------------------------------------------------
# Dashboard tổng quan: trả lời 3 câu hỏi của người quản lý trong MỘT lần gọi API.
#   1) Hôm nay shop thế nào?  2) Hệ thống rủi ro đang can thiệp gì?  3) Có gì cần xử lý ngay?
# So sánh với kỳ trước có cùng độ dài (ví dụ 7 ngày này với 7 ngày trước đó).
# Ngày được tính theo giờ Việt Nam (UTC+7), vì CSDL lưu giờ UTC.
# ---------------------------------------------------------------------------------------------
VN_OFFSET_HOURS = 7
EXCLUDED_ORDER_STATUSES = ("CANCELLED", "REJECTED")  # không tính vào giá trị đơn hàng
STALE_CASE_HOURS = 24  # case chưa ai nhận quá ngưỡng này là "quá hạn"


def _shop_period(db: Session, start, end) -> dict:
    row = db.execute(text("""
        SELECT COUNT(*), COALESCE(SUM(total), 0), COALESCE(SUM(payment_method = 'COD'), 0),
               COALESCE(SUM(voucher_code IS NOT NULL), 0)
        FROM orders WHERE created_at >= :a AND created_at < :b AND status NOT IN :excluded
    """).bindparams(bindparam("excluded", expanding=True)),
        {"a": start, "b": end, "excluded": list(EXCLUDED_ORDER_STATUSES)}).one()
    new_customers = db.execute(text(
        "SELECT COUNT(*) FROM users WHERE role = 'customer' AND created_at >= :a AND created_at < :b"
    ), {"a": start, "b": end}).scalar()
    decisions, intervened = db.execute(text("""
        SELECT COUNT(*), COALESCE(SUM(decision <> 'ALLOW'), 0) FROM risk_decisions
        WHERE created_at >= :a AND created_at < :b
    """), {"a": start, "b": end}).one()
    return {
        "orders": int(row[0]), "gmv": int(row[1]), "cod_orders": int(row[2]), "voucher_orders": int(row[3]),
        "new_customers": int(new_customers), "decisions": int(decisions), "intervened": int(intervened),
    }


def dashboard(db: Session, days: int) -> dict:
    now = utcnow()
    since = now - timedelta(days=days)
    prev_since = since - timedelta(days=days)
    local_day = f"DATE(DATE_ADD(created_at, INTERVAL {VN_OFFSET_HOURS} HOUR))"

    # Chuỗi theo ngày: điền đủ mọi ngày (kể cả ngày không có dữ liệu) để biểu đồ không bị "nhảy cóc"
    today = (now + timedelta(hours=VN_OFFSET_HOURS)).date()
    dates = [today - timedelta(days=i) for i in range(days - 1, -1, -1)]
    series = {d: {"date": d.isoformat(), "orders": 0, "gmv": 0, "ALLOW": 0, "ALLOW_WITH_RESTRICTION": 0,
                  "REVIEW": 0, "BLOCK": 0} for d in dates}
    for day, n, gmv in db.execute(text(f"""
        SELECT {local_day}, COUNT(*), COALESCE(SUM(total), 0) FROM orders
        WHERE created_at >= :since AND status NOT IN :excluded GROUP BY 1
    """).bindparams(bindparam("excluded", expanding=True)),
            {"since": since, "excluded": list(EXCLUDED_ORDER_STATUSES)}):
        if day in series:
            series[day]["orders"], series[day]["gmv"] = int(n), int(gmv)
    for day, decision, n in db.execute(text(f"""
        SELECT {local_day}, decision, COUNT(*) FROM risk_decisions WHERE created_at >= :since GROUP BY 1, 2
    """), {"since": since}):
        if day in series and decision in series[day]:
            series[day][decision] = int(n)

    latencies = sorted(float(r[0]) for r in db.execute(text(
        "SELECT latency_ms FROM risk_decisions WHERE created_at >= :since AND error IS NULL"), {"since": since}))

    top_rules = [
        {"code": code, "name": name, "hits": int(hits)}
        for code, name, hits in db.execute(text("""
            SELECT h.rule_code, MAX(r.name), COUNT(*) FROM rule_hits h
            JOIN risk_decisions d ON d.id = h.decision_id
            LEFT JOIN rules r ON r.code = h.rule_code
            WHERE d.created_at >= :since GROUP BY h.rule_code ORDER BY 3 DESC LIMIT 5
        """), {"since": since})
    ]

    cases = dict(db.execute(text("SELECT status, COUNT(*) FROM risk_cases WHERE status IN ('OPEN', 'IN_REVIEW') GROUP BY status")).all())
    attention = {
        "open_cases": int(cases.get("OPEN", 0)),
        "in_review_cases": int(cases.get("IN_REVIEW", 0)),
        "stale_cases": int(db.execute(text(
            "SELECT COUNT(*) FROM risk_cases WHERE status = 'OPEN' AND opened_at < :t"
        ), {"t": now - timedelta(hours=STALE_CASE_HOURS)}).scalar()),
        "pending_orders": int(db.execute(text("SELECT COUNT(*) FROM orders WHERE status = 'PENDING_REVIEW'")).scalar()),
        "open_appeals": int(db.execute(text("SELECT COUNT(*) FROM appeals WHERE status = 'OPEN'")).scalar()),
        "failed_jobs": int(db.execute(text("SELECT COUNT(*) FROM jobs WHERE status = 'failed'")).scalar()),
        "risk_errors": int(db.execute(text(
            "SELECT COUNT(*) FROM risk_decisions WHERE created_at >= :since AND error IS NOT NULL"), {"since": since}).scalar()),
    }

    # Các quyết định can thiệp gần nhất (email đã che, như mọi API Console)
    recent = [
        {"public_id": pid, "created_at": created, "context": ctx, "decision": dec, "score": int(score),
         "user_email": mask_email(email), "order_code": order_code, "case_code": case_code}
        for pid, created, ctx, dec, score, email, order_code, case_code in db.execute(text("""
            SELECT d.public_id, d.created_at, d.context, d.decision, d.score, u.email, o.order_code,
                   (SELECT c.case_code FROM case_decisions cd JOIN risk_cases c ON c.id = cd.case_id
                    WHERE cd.decision_id = d.id ORDER BY c.id DESC LIMIT 1)
            FROM risk_decisions d JOIN users u ON u.id = d.user_id LEFT JOIN orders o ON o.id = d.order_id
            WHERE d.decision <> 'ALLOW' ORDER BY d.id DESC LIMIT 6
        """))
    ]

    return {
        "days": days,
        "generated_at": now,
        "current": _shop_period(db, since, now),
        "previous": _shop_period(db, prev_since, since),
        "series": list(series.values()),
        "latency_p95_ms": _percentile(latencies, 95),
        "top_rules": top_rules,
        "attention": attention,
        "recent_interventions": recent,
    }
