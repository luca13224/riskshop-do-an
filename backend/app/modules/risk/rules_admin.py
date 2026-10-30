"""Quản lý luật cho Risk Manager: xem luật, xem lịch sử phiên bản, sửa con số -> tạo PHIÊN BẢN MỚI.

Nguyên tắc an toàn khi sửa:
- Chỉ được sửa CON SỐ (ngưỡng, điểm, giá trị điều kiện) và bật/tắt luật. Không được đổi cấu trúc
  (đặc trưng nào, phép so sánh nào, bao nhiêu bậc): đó là thay đổi logic, phải sửa code và có test.
- Không ghi đè phiên bản cũ: quyết định cũ vẫn trỏ đúng phiên bản đã dùng lúc đó (truy vết được).
- Bắt buộc ghi lý do thay đổi; ghi audit log cùng transaction.
"""

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import utcnow
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.risk.models import RiskDecision, Rule, RuleHit, RuleVersion

POINTS_RANGE = (-100, 100)


def _version_out(v: RuleVersion, author: str | None) -> dict:
    return {
        "version": v.version,
        "params": v.params,
        "contexts": v.contexts,
        "enabled": v.enabled,
        "reason_template": v.reason_template,
        "change_note": v.change_note,
        "created_by_name": author,
        "created_at": v.created_at,
    }


def list_rules(db: Session) -> list[dict]:
    since = utcnow() - timedelta(days=7)
    hits = dict(
        db.execute(
            select(RuleHit.rule_code, func.count())
            .join(RiskDecision, RiskDecision.id == RuleHit.decision_id)
            .where(RiskDecision.created_at >= since)
            .group_by(RuleHit.rule_code)
        ).all()
    )
    rows = db.execute(
        select(Rule, RuleVersion).join(RuleVersion, RuleVersion.id == Rule.active_version_id).order_by(Rule.id)
    ).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "rule_type": r.rule_type,
            "strength": r.strength,
            "policies": r.policies,
            "hit_count_7d": hits.get(r.code, 0),
            "active": _version_out(v, None),
        }
        for r, v in rows
    ]


def _get_rule(db: Session, code: str) -> Rule:
    rule = db.scalar(select(Rule).where(Rule.code == code))
    if rule is None:
        raise AppError("RULE_NOT_FOUND", "Không tìm thấy luật.", 404)
    return rule


def list_versions(db: Session, code: str) -> list[dict]:
    rule = _get_rule(db, code)
    rows = db.execute(
        select(RuleVersion, User.full_name)
        .outerjoin(User, User.id == RuleVersion.created_by)
        .where(RuleVersion.rule_id == rule.id)
        .order_by(RuleVersion.version.desc())
    ).all()
    return [_version_out(v, name) for v, name in rows]


def _check_same_shape(old: Any, new: Any, path: str = "params") -> None:
    """Chỉ cho đổi con số: cùng khóa, cùng số phần tử, chuỗi giữ nguyên, số vẫn là số."""
    def fail(msg: str) -> None:
        raise AppError("INVALID_RULE_PARAMS", f"{path}: {msg}", 422)

    if isinstance(old, dict):
        if not isinstance(new, dict) or set(old) != set(new):
            fail("không được thêm/bớt trường (chỉ được sửa con số)")
        for key in old:
            _check_same_shape(old[key], new[key], f"{path}.{key}")
    elif isinstance(old, list):
        if not isinstance(new, list) or len(old) != len(new):
            fail("không được thêm/bớt bậc hoặc điều kiện")
        for i, (a, b) in enumerate(zip(old, new, strict=True)):
            _check_same_shape(a, b, f"{path}[{i}]")
    elif isinstance(old, bool):
        if not isinstance(new, bool):
            fail("phải là đúng/sai")
    elif isinstance(old, (int, float)):
        if isinstance(new, bool) or not isinstance(new, (int, float)):
            fail("phải là số")
        if path.endswith(".points") and not POINTS_RANGE[0] <= new <= POINTS_RANGE[1]:
            fail(f"điểm phải trong khoảng {POINTS_RANGE[0]}..{POINTS_RANGE[1]}")
        if path.endswith(".gte") and new < 0:
            fail("ngưỡng không được âm")
        if path.endswith(".min_count") and (new < 0 or int(new) != new):
            fail("số mẫu tối thiểu phải là số nguyên không âm")
    elif old != new:
        fail("không được đổi tên đặc trưng, phép so sánh hay độ mạnh (chỉ được sửa con số)")


def create_version(db: Session, actor: User, code: str, params: dict, enabled: bool, change_note: str) -> dict:
    rule = _get_rule(db, code)
    current = db.get(RuleVersion, rule.active_version_id)
    _check_same_shape(current.params, params)
    if params == current.params and enabled == current.enabled:
        raise AppError("NO_CHANGE", "Không có thay đổi nào so với phiên bản hiện tại.", 409)
    version = RuleVersion(
        rule_id=rule.id,
        version=current.version + 1,
        contexts=current.contexts,
        params=params,
        reason_template=current.reason_template,
        enabled=enabled,
        created_by=actor.id,
        change_note=change_note,
    )
    db.add(version)
    db.flush()
    rule.active_version_id = version.id  # từ giờ mọi lần chấm điểm dùng phiên bản mới
    audit.record(
        db, actor_id=actor.id, action="rule.new_version", entity_type="rule", entity_id=code,
        before={"version": current.version, "params": current.params, "enabled": current.enabled},
        after={"version": version.version, "params": params, "enabled": enabled}, note=change_note,
    )
    db.commit()
    return next(r for r in list_rules(db) if r["code"] == code)
