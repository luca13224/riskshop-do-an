"""Bộ luật v1 (theo docs/RULES_V0.md) và ngưỡng của ma trận quyết định.

    python -m app.modules.risk.seed

Chạy lại an toàn: luật đã có thì GIỮ NGUYÊN (không ghi đè phiên bản mà Risk Manager có thể đã sửa).
Mọi con số là lập luận chuyên gia ban đầu, sẽ hiệu chỉnh trên tập dev rồi khóa trước khi chạy tập test.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # noqa: F401  (nạp đủ model để khóa ngoại tới users được nhận ra)
from app.core.db import SessionLocal
from app.modules.risk.models import PAYMENT_OPTIONS, PLACE_ORDER, VOUCHER_APPLY, DecisionPolicy, Rule, RuleVersion

V, C = "voucher", "cod"

RULES = [
    dict(code="VCH_NEW_ACCOUNT", name="R01 · Tài khoản mới dùng mã người mới", rule_type="compound",
         strength="weak", policies=[V], contexts=[VOUCHER_APPLY, PLACE_ORDER],
         params={"conditions": [{"feature": "voucher_new_user", "op": "eq", "value": True},
                                {"feature": "account_age_hours", "op": "lt", "value": 24}], "points": 10},
         reason_template="Tài khoản mới tạo {account_age_hours} giờ dùng mã người mới",
         note="Đổi từ \"voucher tân thủ\" sang \"mã người mới\" cho dễ hiểu (rà soát 05/11)"),
    dict(code="DEV_MULTI_NEW_ACCOUNTS", name="R02 · Nhiều tài khoản mới trên cùng thiết bị", rule_type="count_threshold_tiers",
         strength="strong", policies=[V], contexts=[VOUCHER_APPLY, PLACE_ORDER],
         params={"feature": "new_accounts_on_device_30d", "tiers": [{"gte": 5, "points": 50}, {"gte": 3, "points": 35}]},
         reason_template="{value} tài khoản mới trên cùng thiết bị trong 30 ngày (ngưỡng {threshold})"),
    dict(code="ADDR_MULTI_ACCOUNTS", name="R03 · Nhiều tài khoản cùng địa chỉ giao hàng", rule_type="count_threshold_tiers",
         strength="medium", policies=[V], contexts=[PLACE_ORDER],
         params={"feature": "accounts_on_address_30d", "tiers": [{"gte": 5, "points": 30}, {"gte": 3, "points": 20}]},
         reason_template="{value} tài khoản dùng chung địa chỉ giao hàng trong 30 ngày (ngưỡng {threshold})"),
    dict(code="IP_MULTI_NEW_ACCOUNTS", name="R04 · Nhiều tài khoản mới cùng IP", rule_type="count_threshold_tiers",
         strength="weak", policies=[V], contexts=[VOUCHER_APPLY, PLACE_ORDER],
         params={"feature": "new_accounts_on_ip_24h", "tiers": [{"gte": 3, "points": 10}]},
         reason_template="{value} tài khoản mới cùng IP trong 24 giờ (ngưỡng {threshold}, tín hiệu yếu)"),
    dict(code="VCH_VELOCITY", name="R05 · Thử mã giảm giá liên tục", rule_type="count_threshold_tiers",
         strength="strong", policies=[V], contexts=[VOUCHER_APPLY],
         params={"feature": "voucher_attempts_device_10m", "tiers": [{"gte": 5, "points": 25}]},
         reason_template="{value} lần thử mã giảm giá từ cùng thiết bị trong 10 phút (ngưỡng {threshold})"),
    dict(code="BOT_SPEED", name="R06 · Tốc độ thao tác giống bot", rule_type="compound",
         strength="medium", policies=[V, C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"conditions": [{"feature": "signup_to_checkout_sec", "op": "lt", "value": 60},
                                {"feature": "product_views_24h", "op": "eq", "value": 0}], "points": 20},
         reason_template="Đặt hàng {signup_to_checkout_sec} giây sau khi đăng ký, chưa xem sản phẩm nào"),
    dict(code="COD_FAIL_RATE", name="R07 · Tỷ lệ giao COD thất bại cao", rule_type="rate_threshold_tiers",
         strength="medium", policies=[C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"rate_feature": "cod_fail_rate_smoothed", "count_feature": "cod_finished", "min_count": 3,
                 "tiers": [{"gte": 0.30, "points": 45, "strength": "strong"}, {"gte": 0.20, "points": 40}]},
         reason_template="Tỷ lệ giao COD thất bại {rate} trên {count} đơn (ngưỡng {threshold})",
         # ADR-014: bậc 0,20 (gấp đôi mức nền 10% của phép làm mượt) từ +25 lên +40 để TỰ MÌNH đủ ngưỡng ẩn COD.
         # Kẻ bùng hàng ít đơn (2/3, 3/5 thất bại) bị làm mượt xuống 0,23–0,29 nên trước đây lọt.
         note="ADR-014: bậc 0,20 → +40, đủ để ẩn COD (chỉ còn trả trước)"),
    dict(code="COD_HIGH_VALUE_LOW_HISTORY", name="R08 · COD giá trị cao, ít lịch sử", rule_type="compound",
         strength="medium", policies=[C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"conditions": [{"feature": "payment_cod", "op": "eq", "value": True},
                                {"feature": "delivered_orders", "op": "lt", "value": 2}],
                 "tiers": {"feature": "order_value", "levels": [
                     {"gte": 5_000_000, "points": 70, "strength": "strong"}, {"gte": 3_000_000, "points": 40}]}},
         reason_template="Đơn COD {value}đ từ tài khoản mới có {delivered_orders} đơn giao thành công"),
    dict(code="GOOD_HISTORY", name="R09 · Khách uy tín (luật tích cực)", rule_type="compound",
         strength="positive", policies=[C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"conditions": [{"feature": "delivered_orders", "op": "gte", "value": 10},
                                {"feature": "fail_rate_raw", "op": "lte", "value": 0.05}], "points": -30},
         reason_template="Khách uy tín: {delivered_orders} đơn giao thành công"),
    dict(code="COD_OPEN_ORDERS", name="R10 · Treo nhiều đơn COD", rule_type="count_threshold_tiers",
         strength="medium", policies=[C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"feature": "open_cod_orders", "tiers": [{"gte": 3, "points": 25}]},
         reason_template="{value} đơn COD đang chờ giao (ngưỡng {threshold})"),
    # ---- Bộ luật v2 (2026-10-31, docs/reviews/2026-10-31_RISK_V2_DESIGN.md) ----
    # Farm phân tán: mỗi tài khoản một máy, một mạng, nhưng cùng giao về một nhà. Một mình mỗi tín hiệu thì yếu;
    # nhìn cả cụm quanh địa chỉ mới thấy: nhiều tài khoản mới, mỗi người vào mạng từ một nơi khác nhau.
    # Gia đình thật thường chung Wi-Fi nên độ phân tán mạng thấp. Độ mạnh "vừa": chỉ gỡ voucher, không giữ đơn.
    # Ngưỡng 5 (không phải 4 như thiết kế ban đầu): chọn trên tập dev_v2 để giảm gỡ nhầm nhóm ở trọ dùng 4G riêng.
    dict(code="ADDR_VOUCHER_RING", name="R11 · Cụm tài khoản mới cùng địa chỉ, khác mạng", rule_type="compound",
         strength="medium", policies=[V], contexts=[PLACE_ORDER],
         params={"conditions": [{"feature": "voucher_new_user", "op": "eq", "value": True},
                                {"feature": "new_accounts_on_address_7d", "op": "gte", "value": 5},
                                {"feature": "address_ip_diversity_7d", "op": "gte", "value": 0.75}], "points": 25},
         reason_template="{new_accounts_on_address_7d} tài khoản mới cùng địa chỉ giao hàng trong 7 ngày, "
                         "độ phân tán mạng {address_ip_diversity_7d}",
         note="Bộ luật v2: cụm tài khoản mới quanh một địa chỉ"),
    # ---- Bộ luật v3 (2026-10-31): dấu hiệu mới cho điểm tin cậy tài khoản (docs/reviews/2026-10-31_TRUST_SCORE_DESIGN.md) ----
    # Chỉ khi một SĐT nhận hàng ở >= 2 địa chỉ: cả nhà chung SĐT ở một địa chỉ thì không trừ (tránh trừ trùng với R03)
    dict(code="PHONE_MULTI_ACCOUNTS", name="R12 · Một SĐT nhận hàng cho nhiều tài khoản ở nhiều địa chỉ", rule_type="compound",
         strength="medium", policies=[V], contexts=[PLACE_ORDER],
         params={"conditions": [{"feature": "addresses_on_phone_30d", "op": "gte", "value": 2}],
                 "tiers": {"feature": "accounts_on_phone_30d", "levels": [{"gte": 5, "points": 25}, {"gte": 3, "points": 15}]}},
         reason_template="{value} tài khoản dùng chung số điện thoại nhận hàng ở {addresses_on_phone_30d} địa chỉ "
                         "trong 30 ngày (ngưỡng {threshold})",
         note="Bộ luật v3: SĐT nhận hàng dùng chung"),
    dict(code="ADDRESS_HOPPING", name="R13 · Đổi địa chỉ giao hàng liên tục", rule_type="count_threshold_tiers",
         strength="weak", policies=[V], contexts=[PLACE_ORDER],
         params={"feature": "distinct_addresses_7d", "tiers": [{"gte": 3, "points": 10}]},
         reason_template="Dùng {value} địa chỉ giao hàng khác nhau trong 7 ngày (ngưỡng {threshold})",
         note="Bộ luật v3: đổi địa chỉ liên tục"),
    dict(code="VOUCHER_SUBSIDY_HIGH", name="R14 · Sàn bù voucher quá nhiều", rule_type="count_threshold_tiers",
         strength="medium", policies=[V], contexts=[VOUCHER_APPLY, PLACE_ORDER],
         params={"feature": "voucher_subsidy_ratio_90d", "tiers": [{"gte": 0.25, "points": 20}, {"gte": 0.15, "points": 10}]},
         reason_template="Tiền giảm bằng voucher bằng {value} tổng tiền hàng trong 90 ngày (ngưỡng {threshold})",
         note="Bộ luật v3: tỷ lệ trợ giá thay cho lãi/lỗ"),
    dict(code="PROFITABLE_CUSTOMER", name="R15 · Khách mua đều, ít phụ thuộc voucher (luật tích cực)", rule_type="compound",
         strength="positive", policies=[V], contexts=[VOUCHER_APPLY, PLACE_ORDER],
         params={"conditions": [{"feature": "delivered_orders", "op": "gte", "value": 3},
                                {"feature": "voucher_subsidy_ratio_90d", "op": "lt", "value": 0.10}], "points": -15},
         reason_template="Khách mua đều: {delivered_orders} đơn giao thành công, ít phụ thuộc voucher",
         note="Bộ luật v3: hồi điểm tin cậy cho khách mang lại doanh thu"),
    # ---- ADR-011: né lệnh khóa bằng tài khoản mới ----
    # Một điểm chung mạnh với tài khoản đang bị ban: trừ đủ mạnh để mã người mới bị khóa (tin cậy < 50) và mở case,
    # nhưng KHÔNG tự khóa thanh toán (bố bị ban, con dùng chung máy). Khóa thanh toán xử lý riêng ở service.
    # ADR-014: tài khoản chưa có đơn giao thành công nào mà đã có từ 2 đơn COD đang chờ giao -> đơn COD thứ 3
    # phải trả trước. Hard negative: khách mới mua nhiều đợt liền nhau (vẫn mua được, chỉ không dùng COD).
    # Độ mạnh "vừa": chỉ ẩn COD, không giữ hay chặn đơn.
    dict(code="COD_OPEN_NEW_ACCOUNT", name="R17 · Tài khoản mới treo nhiều đơn COD", rule_type="compound",
         strength="medium", policies=[C], contexts=[PAYMENT_OPTIONS, PLACE_ORDER],
         params={"conditions": [{"feature": "delivered_orders", "op": "lt", "value": 1},
                                {"feature": "open_cod_orders", "op": "gte", "value": 2}], "points": 40},
         reason_template="Tài khoản chưa nhận đơn nào đã có {open_cod_orders} đơn COD đang chờ giao",
         note="ADR-014: luật mới"),
    # ADR-013: R16 CHỈ trừ điểm tin cậy tài khoản (contexts rỗng: không cộng vào điểm voucher / COD của giao dịch).
    # Chung 1 điểm (người nhà dùng chung máy) thì không bị gỡ mã sớm; kẻ né khóa đi tiếp tới bước đặt hàng, nơi biết
    # đủ thiết bị + SĐT + địa chỉ, và bị khóa thanh toán khi chung >= 2 điểm (service._linked_enforcement).
    # 35 điểm (trước là 45, chọn trên dev_v3): cộng R01 (10) vẫn còn 55 >= 50 = min_trust của NGUOIMOI.
    dict(code="LINKED_TO_BANNED", name="R16 · Dùng chung thiết bị / SĐT / địa chỉ với tài khoản đang bị khóa",
         rule_type="count_threshold_tiers", strength="medium", policies=[V, C],
         contexts=[],
         params={"feature": "banned_link_types_90d", "tiers": [{"gte": 2, "points": 60}, {"gte": 1, "points": 35}]},
         reason_template="Dùng chung {value} loại điểm (thiết bị, SĐT, địa chỉ) với tài khoản đang bị khóa "
                         "(ngưỡng {threshold})",
         note="ADR-013: chỉ trừ điểm tin cậy; 1 điểm chung = 35"),
]

# Bậc điểm tin cậy (bộ luật v3): dưới case_below thì mở case lúc đặt hàng; từ cod_off_at_or_below trở xuống thì tắt COD.
# Mã giảm giá bị khóa theo min_trust của từng mã (bảng vouchers). Bỏ khóa "trust" là tắt cả lớp 1 (dùng cho thực nghiệm).
# Bộ luật v3.1 (2026-11-03, ADR-012): luật chỉ mô tả ĐƠN đang đặt (giá trị, phương thức) không trừ vào điểm tin cậy
# TÀI KHOẢN. Nó vẫn tính vào điểm COD của chính giao dịch đó. Trước v3.1, khách mới mua COD giá trị cao rớt xuống ~30 điểm.
TRUST = {"case_below": 30, "cod_off_at_or_below": 0,
         "exclude_rules": ["COD_HIGH_VALUE_LOW_HISTORY", "COD_OPEN_NEW_ACCOUNT"]}  # R17 cũng chỉ mô tả đơn đang đặt (ADR-014)

POLICIES = {
    VOUCHER_APPLY: {V: {"restrict": 50, "open_case": 80}, "trust": TRUST},
    PAYMENT_OPTIONS: {C: {"restrict": 40, "review": 70, "block": 90}, "trust": TRUST},
    PLACE_ORDER: {V: {"restrict": 50, "open_case": 80}, C: {"restrict": 40, "review": 70, "block": 90}, "trust": TRUST},
}


def seed_rules(db: Session) -> int:
    """Tạo luật còn thiếu. Luật đã có mà nội dung trong file này khác bản đang dùng
    thì tạo PHIÊN BẢN MỚI (không sửa đè phiên bản cũ, để quyết định cũ vẫn truy vết được)."""
    created = 0
    for spec in RULES:
        rule = db.scalar(select(Rule).where(Rule.code == spec["code"]))
        if rule:
            rule.name = spec["name"]  # tên chỉ để hiển thị, không ảnh hưởng chấm điểm nên cập nhật thẳng
            current = db.get(RuleVersion, rule.active_version_id)
            if (current.contexts, current.params, current.reason_template) != (
                spec["contexts"], spec["params"], spec["reason_template"]
            ):
                version = RuleVersion(rule_id=rule.id, version=current.version + 1, contexts=spec["contexts"],
                                      params=spec["params"], reason_template=spec["reason_template"],
                                      change_note=spec.get("note", "Cập nhật từ seed"))
                db.add(version)
                db.flush()
                rule.active_version_id = version.id
                created += 1
            continue
        rule = Rule(code=spec["code"], name=spec["name"], rule_type=spec["rule_type"],
                    strength=spec["strength"], policies=spec["policies"])
        db.add(rule)
        db.flush()
        version = RuleVersion(rule_id=rule.id, version=1, contexts=spec["contexts"], params=spec["params"],
                              reason_template=spec["reason_template"],
                              change_note=spec.get("note", "Phiên bản đầu (RULES_V0)"))
        db.add(version)
        db.flush()
        rule.active_version_id = version.id
        created += 1
    for context, thresholds in POLICIES.items():
        active = db.scalar(select(DecisionPolicy).where(DecisionPolicy.context == context,
                                                        DecisionPolicy.is_active.is_(True)))
        if active is None or active.thresholds != thresholds:
            if active:
                active.is_active = False
            db.add(DecisionPolicy(context=context, version=(active.version + 1) if active else 1,
                                  thresholds=thresholds))
    db.commit()
    return created


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    with SessionLocal() as session:
        print(f"Đã thêm hoặc nâng phiên bản {seed_rules(session)} luật (tổng {len(RULES)} luật).")
