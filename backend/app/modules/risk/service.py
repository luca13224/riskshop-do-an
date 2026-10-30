"""Risk Engine: đặc trưng -> luật -> điểm theo từng chính sách -> ma trận quyết định -> hành động.

Hàm công khai cho module khác:
- evaluate(db, request) -> RiskResult     chấm điểm (chưa lưu)
- record(db, result, order_id=None)       lưu quyết định + luật đã khớp (bên gọi commit)

Bên gọi chủ động lưu quyết định, vì khi checkout bị từ chối, transaction đặt hàng phải rollback
nhưng quyết định vẫn phải được lưu lại để truy vết. Xem cách dùng trong cart/service.py, order/service.py.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field

from sqlalchemy import bindparam, select, text
from sqlalchemy.orm import Session

from app.core import jobs
from app.core.config import get_settings
from app.core.time import utcnow
from app.modules.auth import service as auth_service
from app.modules.auth.models import User
from app.modules.auth.security import hash_ip
from app.modules.risk import features as feature_store
from app.modules.risk import rules as rule_types
from app.modules.risk.models import (
    ALLOW,
    ALLOW_WITH_RESTRICTION,
    BLOCK,
    PAYMENT_OPTIONS,
    PLACE_ORDER,
    REVIEW,
    SEVERITY,
    VOUCHER_APPLY,
    DecisionPolicy,
    RiskDecision,
    Rule,
    RuleHit,
    RuleVersion,
)

log = logging.getLogger("risk")

VOUCHER, COD = "voucher", "cod"
OPEN_CASE_JOB = "open_case"

MESSAGES = {
    "remove_voucher": "Mã giảm giá không áp dụng được cho đơn hàng này.",
    "disable_cod": "Đơn hàng này hỗ trợ thanh toán trước.",
    "block": "Hiện chưa thể xử lý đơn hàng. Vui lòng liên hệ bộ phận hỗ trợ.",
}

# Đơn COD từ mức này trở lên: nếu Risk Engine lỗi thì KHÔNG cho COD (fail-closed). Còn lại fail-open.
FAIL_CLOSED_COD_VALUE = 3_000_000


@dataclass(frozen=True)
class EvaluationRequest:
    context: str  # voucher_apply | payment_options | place_order
    user: User
    client: auth_service.ClientContext
    order_value: int
    voucher_code: str | None = None
    voucher_new_user: bool | None = None
    payment_method: str | None = None  # COD | PREPAID
    address_hash: str | None = None


@dataclass
class Hit:
    rule_version_id: int
    rule_code: str
    points: int
    strength: str
    policies: list[str]
    observed: dict
    reason_text: str


@dataclass
class RiskResult:
    request: EvaluationRequest
    decision: str
    score: int
    policy_scores: dict[str, int]
    actions: dict[str, bool]
    customer_message: str
    hits: list[Hit] = field(default_factory=list)
    features: dict = field(default_factory=dict)
    policy_id: int | None = None
    latency_ms: float = 0.0
    error: str | None = None


def _active_policies(req: EvaluationRequest) -> list[str]:
    """Chính sách nào đang bị "đụng" tới trong lần đánh giá này."""
    if req.context == VOUCHER_APPLY:
        return [VOUCHER]
    if req.context == PAYMENT_OPTIONS:
        return [COD]
    policies = []
    if req.voucher_code:
        policies.append(VOUCHER)
    if req.payment_method == "COD":
        policies.append(COD)
    return policies


def _load_rules(db: Session, context: str) -> list[tuple[Rule, RuleVersion]]:
    rows = db.execute(
        select(Rule, RuleVersion)
        .join(RuleVersion, RuleVersion.id == Rule.active_version_id)
        .where(RuleVersion.enabled.is_(True))
    ).all()
    return [(r, v) for r, v in rows if context in v.contexts]


def _load_policy(db: Session, context: str) -> DecisionPolicy | None:
    return db.scalar(
        select(DecisionPolicy)
        .where(DecisionPolicy.context == context, DecisionPolicy.is_active.is_(True))
        .order_by(DecisionPolicy.version.desc())
    )


def decide(context: str, policy_scores: dict[str, int], strong_counts: dict[str, int], thresholds: dict) -> tuple[str, dict]:
    """Ma trận quyết định (RULES_V0 mục 4). Hàm thuần, test riêng được.

    Mỗi chính sách có điểm riêng; hành động tương ứng theo chính sách đó.
    payment_options dùng CÙNG ngưỡng với place_order để giao diện không "nói một đằng, làm một nẻo".
    REVIEW / BLOCK luôn cần luật MẠNH, không bao giờ chỉ vì nhiều tín hiệu yếu cộng lại.
    """
    actions = {"remove_voucher": False, "disable_cod": False, "hold_order": False, "block": False, "open_case": False}
    decision = ALLOW

    def escalate(new: str) -> None:
        nonlocal decision
        if SEVERITY[new] > SEVERITY[decision]:
            decision = new

    v = thresholds.get(VOUCHER)
    if v is not None and VOUCHER in policy_scores:
        score = policy_scores[VOUCHER]
        if score >= v["restrict"]:
            actions["remove_voucher"] = True
            escalate(ALLOW_WITH_RESTRICTION)
        if score >= v.get("open_case", 101):
            actions["open_case"] = True

    c = thresholds.get(COD)
    if c is not None and COD in policy_scores:
        score, strong = policy_scores[COD], strong_counts.get(COD, 0)
        if score >= c.get("block", 101) and strong >= 2:
            if context == PLACE_ORDER:
                actions["block"] = actions["open_case"] = True
                escalate(BLOCK)
            else:  # payment_options: đơn này sẽ bị chặn -> ẩn COD ngay từ đầu
                actions["disable_cod"] = True
                escalate(ALLOW_WITH_RESTRICTION)
        elif score >= c.get("review", 101) and strong >= 1:
            if context == PLACE_ORDER:
                actions["hold_order"] = actions["open_case"] = True
                escalate(REVIEW)
            # payment_options: đơn sẽ được GIỮ chờ duyệt, nên vẫn cho chọn COD (không mâu thuẫn với lúc đặt)
        elif score >= c["restrict"]:
            actions["disable_cod"] = True
            escalate(ALLOW_WITH_RESTRICTION)
    return decision, actions


def _customer_message(actions: dict) -> str:
    if actions["block"]:
        return MESSAGES["block"]
    parts = [MESSAGES[k] for k in ("remove_voucher", "disable_cod") if actions[k]]
    return " ".join(parts)


def evaluate(db: Session, req: EvaluationRequest) -> RiskResult:
    """Chấm điểm. Không bao giờ ném lỗi ra ngoài: nếu engine lỗi thì trả kết quả dự phòng (fail-open/closed)."""
    started = time.perf_counter()
    try:
        result = _evaluate(db, req)
    except Exception as exc:  # noqa: BLE001 - lỗi engine không được làm sập luồng mua hàng
        log.exception("Risk engine error context=%s user=%s", req.context, req.user.id)
        result = _fallback(req, f"{type(exc).__name__}: {exc}"[:255])
    result.latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return result


def _evaluate(db: Session, req: EvaluationRequest) -> RiskResult:
    # Cập nhật liên kết tài khoản - thiết bị - IP trước khi đếm, để số liệu luôn mới nhất
    device_id = auth_service.record_client(db, req.user, req.client)
    ip_hash = hash_ip(req.client.ip, get_settings().ip_hash_secret) if req.client.ip else None

    features = feature_store.compute(
        db,
        feature_store.FeatureInput(
            user_id=req.user.id,
            user_created_at=req.user.created_at,
            device_id=device_id,
            ip_hash=ip_hash,
            address_hash=req.address_hash,
            voucher_new_user=req.voucher_new_user,
            payment_cod=None if req.payment_method is None else req.payment_method == "COD",
            order_value=req.order_value,
            as_of=utcnow(),
        ),
    )

    features["voucher_code"] = req.voucher_code  # lưu lại để báo cáo ước tính giá trị voucher ngăn được
    active = _active_policies(req)
    hits: list[Hit] = []
    for rule, version in _load_rules(db, req.context):
        policies = [p for p in rule.policies if p in active]
        if not policies:
            continue
        match = rule_types.evaluate(rule.rule_type, version.params, features)
        if match is None:
            continue
        hits.append(
            Hit(
                rule_version_id=version.id,
                rule_code=rule.code,
                points=match.points,
                strength=match.strength or rule.strength,
                policies=policies,
                observed=match.observed,
                reason_text=rule_types.format_reason(version.reason_template, match.observed),
            )
        )

    policy_scores = {p: max(0, min(100, sum(h.points for h in hits if p in h.policies))) for p in active}
    strong_counts = {p: sum(1 for h in hits if p in h.policies and h.strength == "strong") for p in active}
    policy = _load_policy(db, req.context)
    decision, actions = decide(req.context, policy_scores, strong_counts, policy.thresholds if policy else {})
    return RiskResult(
        request=req,
        decision=decision,
        score=max(policy_scores.values(), default=0),
        policy_scores=policy_scores,
        actions=actions,
        customer_message=_customer_message(actions),
        hits=hits,
        features=features,
        policy_id=policy.id if policy else None,
    )


def _fallback(req: EvaluationRequest, error: str) -> RiskResult:
    actions = {"remove_voucher": False, "disable_cod": False, "hold_order": False, "block": False, "open_case": False}
    decision = ALLOW
    # Fail-closed cho COD giá trị cao: thà yêu cầu trả trước còn hơn để lọt rủi ro lớn
    if req.context in (PLACE_ORDER, PAYMENT_OPTIONS) and req.payment_method == "COD" and req.order_value >= FAIL_CLOSED_COD_VALUE:
        actions["disable_cod"] = True
        decision = ALLOW_WITH_RESTRICTION
    return RiskResult(
        request=req, decision=decision, score=0, policy_scores={}, actions=actions,
        customer_message=_customer_message(actions), error=error,
    )


def record(db: Session, result: RiskResult, order_id: int | None = None) -> str:
    """Lưu quyết định và các luật đã khớp. Trả về public_id. Bên gọi chịu trách nhiệm commit."""
    decision = RiskDecision(
        public_id=str(uuid.uuid4()),
        context=result.request.context,
        user_id=result.request.user.id,
        order_id=order_id,
        score=result.score,
        policy_scores=result.policy_scores,
        decision=result.decision,
        actions=result.actions,
        features_snapshot=result.features,
        policy_id=result.policy_id,
        latency_ms=result.latency_ms,
        error=result.error,
    )
    db.add(decision)
    db.flush()
    for h in result.hits:
        db.add(
            RuleHit(
                decision_id=decision.id,
                rule_version_id=h.rule_version_id,
                rule_code=h.rule_code,
                points=h.points,
                strength=h.strength,
                observed=h.observed,
                reason_text=h.reason_text,
            )
        )
    db.flush()
    if result.actions.get("open_case"):
        # Mở case BẤT ĐỒNG BỘ: worker làm sau, không làm chậm luồng mua hàng.
        # Việc được ghi cùng transaction với quyết định, nên không bao giờ "lưu quyết định mà mất việc".
        jobs.enqueue(db, OPEN_CASE_JOB, {"decision_id": decision.id})
    return decision.public_id


# ---------- Dành cho Console ----------

def list_recent(db: Session, limit: int = 50, after_id: int | None = None) -> list[dict]:
    """Các quyết định mới nhất kèm luật đã khớp (cho Live Monitor)."""
    query = select(RiskDecision, User.email, User.full_name).join(User, User.id == RiskDecision.user_id)
    if after_id:
        query = query.where(RiskDecision.id > after_id)
    return _serialize(db, db.execute(query.order_by(RiskDecision.id.desc()).limit(limit)).all())


def decisions_by_ids(db: Session, ids: list[int]) -> list[dict]:
    """Hàm công khai cho module cases: các quyết định theo id, mới nhất trước."""
    if not ids:
        return []
    query = (
        select(RiskDecision, User.email, User.full_name)
        .join(User, User.id == RiskDecision.user_id)
        .where(RiskDecision.id.in_(ids))
        .order_by(RiskDecision.id.desc())
    )
    return _serialize(db, db.execute(query).all())


def decision_info(db: Session, decision_id: int) -> RiskDecision | None:
    """Hàm công khai cho module cases: đọc một quyết định (chỉ đọc)."""
    return db.get(RiskDecision, decision_id)


def _serialize(db: Session, rows) -> list[dict]:
    ids = [d.id for d, _, _ in rows]
    hits_by_decision: dict[int, list[dict]] = {i: [] for i in ids}
    if ids:
        for h in db.scalars(select(RuleHit).where(RuleHit.decision_id.in_(ids)).order_by(RuleHit.points.desc())):
            hits_by_decision[h.decision_id].append(
                {"rule_code": h.rule_code, "points": h.points, "strength": h.strength, "reason_text": h.reason_text}
            )
    order_codes = {}
    order_ids = [d.order_id for d, _, _ in rows if d.order_id]
    if order_ids:
        order_codes = dict(
            db.execute(
                text("SELECT id, order_code FROM orders WHERE id IN :ids").bindparams(bindparam("ids", expanding=True)),
                {"ids": order_ids},
            ).all()
        )
    return [
        {
            "id": d.id,
            "public_id": d.public_id,
            "created_at": d.created_at,
            "context": d.context,
            "decision": d.decision,
            "score": d.score,
            "policy_scores": d.policy_scores,
            "actions": d.actions,
            "latency_ms": d.latency_ms,
            "error": d.error,
            "user_id": d.user_id,
            "user_email": email,
            "user_name": name,
            "order_code": order_codes.get(d.order_id),
            "hits": hits_by_decision[d.id],
        }
        for d, email, name in rows
    ]
