"""Test bộ nhớ đệm luật và ngưỡng (ADR-017): đọc từ cache trong thời hạn, làm mới khi hết hạn hoặc bị xóa."""

from sqlalchemy import select

from app.modules.risk import service
from app.modules.risk.models import Rule, RuleVersion
from tests.test_risk_scenarios import shop  # noqa: F401 (fixture shop)


def r02_version(db) -> RuleVersion:
    rule = db.scalar(select(Rule).where(Rule.code == "DEV_MULTI_NEW_ACCOUNTS"))
    return db.get(RuleVersion, rule.active_version_id)


def codes(db) -> set[str]:
    return {r.code for r, _ in service._load_rules(db, None)}


def test_cache_serves_snapshot_until_invalidated(shop, db):
    assert "DEV_MULTI_NEW_ACCOUNTS" in codes(db)
    r02_version(db).enabled = False  # sửa thẳng trong CSDL, không qua API
    db.commit()
    assert "DEV_MULTI_NEW_ACCOUNTS" in codes(db)  # còn trong hạn: vẫn bản cũ
    service.invalidate_rule_cache()
    assert "DEV_MULTI_NEW_ACCOUNTS" not in codes(db)


def test_cache_refreshes_after_expiry(shop, db, monkeypatch):
    codes(db)
    r02_version(db).enabled = False
    db.commit()
    monkeypatch.setattr(service, "RULE_CACHE_SECONDS", 0.0)  # coi như đã hết hạn
    assert "DEV_MULTI_NEW_ACCOUNTS" not in codes(db)


def test_policy_comes_from_cache_with_highest_active_version(shop, db):
    policy = service._load_policy(db, "place_order")
    assert policy is not None and "voucher" in policy.thresholds and "cod" in policy.thresholds
    assert service._load_policy(db, "khong_co") is None
