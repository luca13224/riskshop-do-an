"""Bộ sinh lịch sử demo: chạy trên CSDL test, kiểm tra dữ liệu được dời đúng về các ngày trước."""

from datetime import timedelta

from sqlalchemy import func, select, text

from app.core.time import utcnow
from app.modules.lab.reset import reset
from app.modules.order.models import Order
from app.modules.risk.models import RiskDecision
from conftest import TestSession
from simulator.history import run


def test_history_spreads_activity_over_past_days(db):
    reset(db)
    totals = run(days=3, seed=1, per_day=0.03, progress=lambda _: None, session_factory=TestSession)
    assert totals["server_errors"] == []
    db.rollback()
    assert totals["accounts"] > 0 and totals["orders"] > 0

    now = utcnow()
    # Mọi quyết định và đơn của lịch sử nằm trong 3 ngày trước (theo giờ VN), không có cái nào ở tương lai
    days = {d for (d,) in db.execute(text(
        "SELECT DISTINCT DATE(DATE_ADD(created_at, INTERVAL 7 HOUR)) FROM risk_decisions"))}
    assert len(days) >= 2
    assert db.scalar(select(func.max(RiskDecision.created_at))) <= now
    assert db.scalar(select(func.min(RiskDecision.created_at))) >= now - timedelta(days=4)
    # Đơn ngày cũ đã được giao (thành công hoặc thất bại), không còn treo ở CONFIRMED
    assert not db.scalar(select(func.count()).where(Order.status == "CONFIRMED"))
    # Tồn kho trả về số chuẩn sau khi chạy
    assert db.scalar(text("SELECT MAX(stock) FROM products")) < 100000
