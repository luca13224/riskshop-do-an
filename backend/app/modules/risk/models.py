from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, CHAR, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.time import utcnow

# Context: ba điểm kiểm soát
VOUCHER_APPLY = "voucher_apply"
PAYMENT_OPTIONS = "payment_options"
PLACE_ORDER = "place_order"

# Quyết định, xếp theo mức nghiêm trọng tăng dần
ALLOW = "ALLOW"
ALLOW_WITH_RESTRICTION = "ALLOW_WITH_RESTRICTION"
REVIEW = "REVIEW"
BLOCK = "BLOCK"
SEVERITY = {ALLOW: 0, ALLOW_WITH_RESTRICTION: 1, REVIEW: 2, BLOCK: 3}


class Rule(Base):
    """Danh tính của một luật. Nội dung (tham số, điểm) nằm ở RuleVersion."""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    rule_type: Mapped[str] = mapped_column(String(32))
    strength: Mapped[str] = mapped_column(String(10))  # strong | medium | weak | positive
    policies: Mapped[list] = mapped_column(JSON)  # ["voucher"], ["cod"] hoặc cả hai
    # Không đặt khóa ngoại để tránh vòng tham chiếu rules <-> rule_versions
    active_version_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RuleVersion(Base):
    """Một phiên bản luật. Sửa luật = tạo phiên bản mới; phiên bản cũ giữ nguyên để truy vết."""

    __tablename__ = "rule_versions"
    __table_args__ = (UniqueConstraint("rule_id", "version", name="uq_rule_versions_rule_version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"))
    version: Mapped[int] = mapped_column(Integer)
    contexts: Mapped[list] = mapped_column(JSON)
    params: Mapped[dict] = mapped_column(JSON)
    reason_template: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    change_note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class DecisionPolicy(Base):
    """Ngưỡng của ma trận quyết định cho một context, có phiên bản."""

    __tablename__ = "decision_policies"
    __table_args__ = (UniqueConstraint("context", "version", name="uq_decision_policies_context_version"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    context: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    thresholds: Mapped[dict] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RiskDecision(Base):
    """Một quyết định của Risk Engine. CHỈ GHI THÊM: không có code nào sửa hoặc xóa dòng này.
    Ghi đè (override) của nhân viên sẽ tạo quyết định mới trỏ về quyết định cũ."""

    __tablename__ = "risk_decisions"
    __table_args__ = (
        Index("ix_risk_decisions_created", "created_at"),
        Index("ix_risk_decisions_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(CHAR(36), unique=True)
    context: Mapped[str] = mapped_column(String(32))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    score: Mapped[int] = mapped_column(Integer)
    policy_scores: Mapped[dict] = mapped_column(JSON)
    decision: Mapped[str] = mapped_column(String(32))
    actions: Mapped[dict] = mapped_column(JSON)
    features_snapshot: Mapped[dict] = mapped_column(JSON)
    policy_id: Mapped[int | None] = mapped_column(ForeignKey("decision_policies.id"))
    latency_ms: Mapped[float] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(String(255))
    overrides_decision_id: Mapped[int | None] = mapped_column(ForeignKey("risk_decisions.id"))
    decided_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    override_reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class RuleHit(Base):
    """Một luật đã khớp trong một quyết định: bao nhiêu điểm, vì sao (giá trị thực tế, ngưỡng)."""

    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("risk_decisions.id"), index=True)
    rule_version_id: Mapped[int] = mapped_column(ForeignKey("rule_versions.id"))
    rule_code: Mapped[str] = mapped_column(String(64))
    points: Mapped[int] = mapped_column(Integer)
    strength: Mapped[str] = mapped_column(String(10))
    observed: Mapped[dict] = mapped_column(JSON)
    reason_text: Mapped[str] = mapped_column(String(500))


class RiskAllowlist(Base):
    """Miễn trừ một chính sách (voucher/cod) cho một khách trong một khoảng thời gian.

    Sinh ra khi khiếu nại được chấp nhận (ADR-006). Luật vẫn chạy và vẫn ghi lại đã khớp,
    chỉ có HÀNH ĐỘNG hạn chế của chính sách đó được bỏ qua, nên vẫn giải thích và kiểm tra lại được.
    """

    __tablename__ = "risk_allowlist"
    __table_args__ = (Index("ix_risk_allowlist_user_policy_exp", "user_id", "policy", "expires_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    policy: Mapped[str] = mapped_column(String(10))  # voucher | cod
    reason: Mapped[str] = mapped_column(String(255))
    source_ref: Mapped[str | None] = mapped_column(String(32))  # ví dụ mã khiếu nại
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


# Loại khóa tài khoản (ADR-010)
PURCHASE_COOLDOWN = "purchase_cooldown"  # tạm khóa mua hàng có thời hạn
PURCHASE_BAN = "purchase_ban"  # khóa mua hàng vô thời hạn (chỉ gỡ khi có người xem xét lại)


class AccountRestriction(Base):
    """Khóa QUYỀN MUA HÀNG của một tài khoản (vẫn đăng nhập, xem đơn, gửi khiếu nại được).

    Sinh tự động khi tài khoản cố đặt hàng lặp lại sau nhiều lần bị từ chối (ADR-010), hoặc do nhân viên.
    Không bao giờ xóa: gỡ khóa là ghi lifted_at / lifted_by / lift_reason, để truy vết và kiểm toán.
    """

    __tablename__ = "account_restrictions"
    __table_args__ = (Index("ix_account_restrictions_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(20))  # purchase_cooldown | purchase_ban
    reason: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(10), default="auto")  # auto | staff
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("risk_decisions.id"))  # quyết định kích hoạt
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)  # NULL: vô thời hạn
    lifted_at: Mapped[datetime | None] = mapped_column(DateTime)
    lifted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    lift_reason: Mapped[str | None] = mapped_column(String(255))
