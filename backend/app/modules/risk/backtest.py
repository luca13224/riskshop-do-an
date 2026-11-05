"""Chạy thử luật trước khi bật (shadow test / backtest).

Câu hỏi: "Nếu luật X dùng tham số mới thì các quyết định trong N ngày qua sẽ khác đi thế nào, ai bị ảnh hưởng?"
Chỉ ĐỌC, không ghi gì: nhân viên nào cũng chạy được (sửa luật thật vẫn chỉ Risk Manager / Admin).

Cách phát lại một quyết định cũ:
1. Lấy các luật đã khớp (rule_hits) và ảnh chụp đặc trưng (features_snapshot) đã lưu lúc chấm điểm.
2. Bỏ điểm của luật X cũ, tính lại luật X với tham số mới trên chính ảnh chụp đó, cộng lại điểm từng chính sách.
3. Tính lại điểm tin cậy: bỏ phần trừ của X cũ, thêm phần trừ của X mới (nếu X không nằm trong danh sách loại trừ).
4. Chạy lại đúng hàm decide() của Risk Engine với ngưỡng của chính sách đã dùng lúc đó.
So "phát lại bằng luật cũ" với "phát lại bằng luật mới" để chỉ đo tác động của thay đổi.

Giới hạn (trả về cho giao diện hiển thị):
- Chỉ thấy những lần chấm điểm đã xảy ra; không biết kẻ gian sẽ đổi hành vi thế nào khi luật đổi.
- Không phát lại khóa tài khoản (ADR-010/011/015): quyết định đã có khóa liên kết thì coi như không đổi.
- `replay_agreement`: tỷ lệ quyết định mà phát lại bằng luật cũ cho đúng kết quả thật, để biết độ tin cậy.
"""

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.privacy import mask_email
from app.core.time import utcnow
from app.modules.auth.models import User
from app.modules.cases.models import RiskCase
from app.modules.promotion.models import Voucher
from app.modules.risk import rules as rule_types
from app.modules.risk.models import SEVERITY, DecisionPolicy, RiskDecision, Rule, RuleHit, RuleVersion
from app.modules.risk.rules_admin import _check_same_shape, _get_rule
from app.modules.risk.service import TRUST_MAX, decide

MAX_DECISIONS = 20_000
SAMPLE_SIZE = 8


def _replay(d: RiskDecision, hits: list[RuleHit], rule: Rule, match, deduction_new: int | None,
            thresholds: dict, min_trust: dict[str, int | None], trust_excluded: bool,
            policies_of: dict[str, list[str]]) -> str:
    """Quyết định (chỉ phần do luật + điểm tin cậy) khi luật `rule` khớp ra `match` (None = không khớp)."""
    active = set(d.policy_scores or {})
    scores: dict[str, int] = defaultdict(int)
    strong: dict[str, int] = defaultdict(int)
    for h in hits:
        if h.rule_code == rule.code:
            continue
        for p in policies_of.get(h.rule_code, ()):
            if p in active:
                scores[p] += h.points
                strong[p] += h.strength == "strong"
    if match is not None:
        for p in rule.policies:
            if p in active:
                scores[p] += match.points
                strong[p] += (match.strength or rule.strength) == "strong"
    policy_scores = {p: max(0, min(100, scores[p])) for p in active}

    snap = d.features_snapshot or {}
    trust = snap.get("trust_score")
    if trust is not None and not trust_excluded:
        old = (snap.get("trust_deductions") or {}).get(rule.code, 0)
        trust = min(TRUST_MAX, trust + old - (deduction_new or 0))
    decision, _ = decide(d.context, policy_scores, dict(strong), thresholds,
                         frozenset(snap.get("exempt_policies") or ()), trust=trust,
                         voucher_min_trust=min_trust.get(snap.get("voucher_code") or ""))
    return decision



def backtest(db: Session, code: str, params: dict, enabled: bool, days: int) -> dict:
    rule = _get_rule(db, code)
    current = db.get(RuleVersion, rule.active_version_id)
    _check_same_shape(current.params, params)  # cùng ràng buộc như khi tạo phiên bản thật
    policies_of = {c: p for c, p in db.execute(select(Rule.code, Rule.policies)).all()}
    min_trust = {c: t for c, t in db.execute(select(Voucher.code, Voucher.min_trust)).all()}
    thresholds_of = {pid: t for pid, t in db.execute(select(DecisionPolicy.id, DecisionPolicy.thresholds)).all()}

    since = utcnow() - timedelta(days=days)
    decisions = list(db.scalars(
        select(RiskDecision).where(RiskDecision.created_at >= since, RiskDecision.error.is_(None),
                                   RiskDecision.overrides_decision_id.is_(None), RiskDecision.policy_id.is_not(None))
        .order_by(RiskDecision.id.desc()).limit(MAX_DECISIONS)
    ))
    hits_by = defaultdict(list)
    for h in db.scalars(select(RuleHit).where(RuleHit.decision_id.in_([d.id for d in decisions]))) if decisions else []:
        hits_by[h.decision_id].append(h)

    def evaluate(p: dict, on: bool, snap: dict, context: str | None):
        if not on or (context is not None and context not in current.contexts):
            return None
        return rule_types.evaluate(rule.rule_type, p, snap)

    scanned = agree = hits_old = hits_new = 0
    stricter, looser = [], []
    for d in decisions:
        snap = d.features_snapshot or {}
        if snap.get("account_restriction") or snap.get("linked_lock"):
            continue  # đã bị khóa: kết quả không do điểm luật quyết định
        thresholds = thresholds_of.get(d.policy_id) or {}
        trust_cfg = thresholds.get("trust") or {}
        excluded = code in (trust_cfg.get("exclude_rules") or ())
        m_old = evaluate(current.params, current.enabled, snap, d.context)
        m_new = evaluate(params, enabled, snap, d.context)
        t_old, t_new = evaluate(current.params, current.enabled, snap, None), evaluate(params, enabled, snap, None)
        before = _replay(d, hits_by[d.id], rule, m_old, t_old.points if t_old else None, thresholds, min_trust, excluded,
                         policies_of)
        after = _replay(d, hits_by[d.id], rule, m_new, t_new.points if t_new else None, thresholds, min_trust, excluded,
                        policies_of)
        scanned += 1
        agree += before == d.decision
        hits_old += m_old is not None
        hits_new += m_new is not None
        if SEVERITY[after] > SEVERITY[before]:
            stricter.append((d, before, after))
        elif SEVERITY[after] < SEVERITY[before]:
            looser.append((d, before, after))

    return {
        "rule": rule.code,
        "days": days,
        "decisions_scanned": scanned,
        "truncated": len(decisions) == MAX_DECISIONS,
        "replay_agreement": round(agree / scanned, 4) if scanned else None,
        "hits_old": hits_old,
        "hits_new": hits_new,
        "stricter": _summary(db, stricter),
        "looser": _summary(db, looser),
        "limits": [
            "Chỉ phát lại những lần chấm điểm đã xảy ra; không biết kẻ gian sẽ đổi hành vi khi luật đổi.",
            "Không phát lại việc khóa tài khoản; lượt đã có khóa được coi như không đổi.",
        ],
    }


def _summary(db: Session, rows: list[tuple[RiskDecision, str, str]]) -> dict:
    users = {d.user_id for d, _, _ in rows}
    verdict = {}
    if users:
        for uid, status in db.execute(select(RiskCase.primary_user_id, RiskCase.status)
                                      .where(RiskCase.primary_user_id.in_(users))).all():
            if status in ("CONFIRMED_ABUSE", "CLEARED"):
                verdict.setdefault(uid, set()).add(status)
    loyal = {d.user_id for d, _, _ in rows if ((d.features_snapshot or {}).get("delivered_orders") or 0) >= 10}
    emails = dict(db.execute(select(User.id, User.email).where(User.id.in_(users))).all()) if users else {}
    return {
        "decisions": len(rows),
        "accounts": len(users),
        "confirmed_abuse": sum(1 for u in users if "CONFIRMED_ABUSE" in verdict.get(u, ())),
        "cleared": sum(1 for u in users if "CLEARED" in verdict.get(u, ())),
        "loyal": len(loyal),
        "samples": [
            {"public_id": d.public_id, "created_at": d.created_at, "context": d.context,
             "user_email": mask_email(emails.get(d.user_id, "")), "before": before, "after": after}
            for d, before, after in rows[:SAMPLE_SIZE]
        ],
    }
