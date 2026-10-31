"""Test các LOẠI luật và ma trận quyết định: hàm thuần, không cần CSDL (RULES_V0 mục 7)."""

from app.modules.risk import rules
from app.modules.risk.models import ALLOW, ALLOW_WITH_RESTRICTION, BLOCK, PAYMENT_OPTIONS, PLACE_ORDER, REVIEW
from app.modules.risk.seed import POLICIES
from app.modules.risk.service import decide

TIERS = {"feature": "n", "tiers": [{"gte": 5, "points": 50}, {"gte": 3, "points": 35}]}


def test_count_tiers_below_at_and_highest_tier():
    assert rules.count_threshold_tiers(TIERS, {"n": 2}) is None  # dưới ngưỡng
    assert rules.count_threshold_tiers(TIERS, {"n": 3}).points == 35  # đúng ngưỡng
    assert rules.count_threshold_tiers(TIERS, {"n": 7}).points == 50  # bậc cao nhất, không cộng dồn
    assert rules.count_threshold_tiers(TIERS, {"n": None}) is None  # thiếu dữ liệu: không khớp


R07 = {
    "rate_feature": "rate", "count_feature": "count", "min_count": 3,
    "tiers": [{"gte": 0.30, "points": 45, "strength": "strong"}, {"gte": 0.20, "points": 25}],
}


def test_rate_tiers_require_min_samples():
    # Khách mới thất bại 1/1 đơn: tỷ lệ làm mượt (1+1)/(1+10)=0.18 và chưa đủ 3 đơn -> không khớp
    assert rules.rate_threshold_tiers(R07, {"rate": 0.9, "count": 1}) is None
    m = rules.rate_threshold_tiers(R07, {"rate": 5 / 15, "count": 5})  # Khang: 4/5 thất bại
    assert m.points == 45 and m.strength == "strong"
    assert rules.rate_threshold_tiers(R07, {"rate": 0.2, "count": 5}).strength is None  # bậc thường


R08 = {
    "conditions": [{"feature": "cod", "op": "eq", "value": True}, {"feature": "delivered", "op": "lt", "value": 2}],
    "tiers": {"feature": "value", "levels": [
        {"gte": 5_000_000, "points": 70, "strength": "strong"}, {"gte": 3_000_000, "points": 40}]},
}


def test_compound_with_tiers():
    assert rules.compound(R08, {"cod": True, "delivered": 0, "value": 5_490_000}).points == 70
    assert rules.compound(R08, {"cod": True, "delivered": 0, "value": 3_500_000}).points == 40
    assert rules.compound(R08, {"cod": True, "delivered": 0, "value": 1_000_000}) is None
    assert rules.compound(R08, {"cod": True, "delivered": 30, "value": 9_000_000}) is None  # khách quen
    assert rules.compound(R08, {"cod": False, "delivered": 0, "value": 9_000_000}) is None  # trả trước


def test_compound_fixed_points_negative():
    r09 = {"conditions": [{"feature": "d", "op": "gte", "value": 10}], "points": -30}
    assert rules.compound(r09, {"d": 30}).points == -30


def test_reason_formatting():
    text = rules.format_reason("Đơn COD {value}đ, tỷ lệ {rate} (ngưỡng {threshold}) {missing}",
                               {"value": 5_490_000, "rate": 0.3333, "threshold": 0.3})
    assert text == "Đơn COD 5.490.000đ, tỷ lệ 33% (ngưỡng 30%) ?"


# ---------- Ma trận quyết định ----------

def test_voucher_restrict_and_open_case():
    t = POLICIES[PLACE_ORDER]
    assert decide(PLACE_ORDER, {"voucher": 49}, {}, t)[0] == ALLOW
    decision, actions = decide(PLACE_ORDER, {"voucher": 50}, {}, t)
    assert decision == ALLOW_WITH_RESTRICTION and actions["remove_voucher"] and not actions["open_case"]
    assert decide(PLACE_ORDER, {"voucher": 85}, {}, t)[1]["open_case"]


def test_review_and_block_need_strong_rules():
    t = POLICIES[PLACE_ORDER]
    # 70 điểm nhưng không có luật mạnh -> chỉ hạn chế COD, KHÔNG giữ đơn
    assert decide(PLACE_ORDER, {"cod": 70}, {"cod": 0}, t)[0] == ALLOW_WITH_RESTRICTION
    assert decide(PLACE_ORDER, {"cod": 69}, {"cod": 1}, t)[0] == ALLOW_WITH_RESTRICTION
    assert decide(PLACE_ORDER, {"cod": 70}, {"cod": 1}, t)[0] == REVIEW
    assert decide(PLACE_ORDER, {"cod": 95}, {"cod": 1}, t)[0] == REVIEW  # BLOCK cần >= 2 luật mạnh
    decision, actions = decide(PLACE_ORDER, {"cod": 95}, {"cod": 2}, t)
    assert decision == BLOCK and actions["block"]


def test_payment_options_never_reviews():
    # Ở bước xem phương thức thanh toán chưa có đơn để giữ: chỉ ẩn COD
    decision, actions = decide(PAYMENT_OPTIONS, {"cod": 95}, {"cod": 2}, POLICIES[PAYMENT_OPTIONS])
    assert decision == ALLOW_WITH_RESTRICTION and actions["disable_cod"] and not actions["hold_order"]


def test_most_severe_decision_wins():
    decision, actions = decide(PLACE_ORDER, {"voucher": 60, "cod": 75}, {"cod": 1}, POLICIES[PLACE_ORDER])
    assert decision == REVIEW and actions["remove_voucher"] and actions["hold_order"]


# R11 (bộ luật v2): đúng tham số trong seed, kiểm 5 trường hợp của RULES_V0 mục 7
def _r11():
    from app.modules.risk.seed import RULES
    return next(r for r in RULES if r["code"] == "ADDR_VOUCHER_RING")


def test_r11_thresholds_and_hard_negatives():
    p = _r11()["params"]
    base = {"voucher_new_user": True, "new_accounts_on_address_7d": 5, "address_ip_diversity_7d": 0.75}
    assert rules.compound(p, base).points == 25  # đúng ngưỡng
    assert rules.compound(p, {**base, "new_accounts_on_address_7d": 4}) is None  # dưới ngưỡng cụm
    assert rules.compound(p, {**base, "address_ip_diversity_7d": 0.5}) is None  # gia đình chung mạng
    assert rules.compound(p, {**base, "voucher_new_user": None}) is None  # không dùng voucher tân thủ
    assert rules.compound(p, {**base, "new_accounts_on_address_7d": None}) is None  # chưa có địa chỉ
    assert _r11()["contexts"] == ["place_order"] and _r11()["strength"] == "medium"  # không chạy lúc áp mã
