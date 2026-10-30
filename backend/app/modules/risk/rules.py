"""Các LOẠI luật, viết dưới dạng hàm thuần: nhận (tham số, đặc trưng), trả về khớp hay không.

Không đụng CSDL, không có trạng thái, nên test độc lập rất dễ (tests/test_risk_rules.py).
Luật cụ thể (R01..R10) là DỮ LIỆU trong bảng rule_versions, chọn một loại ở đây và điền tham số.
"""

import operator
from dataclasses import dataclass
from typing import Any

OPS = {"lt": operator.lt, "lte": operator.le, "gt": operator.gt, "gte": operator.ge, "eq": operator.eq}


@dataclass(frozen=True)
class Match:
    points: int
    strength: str | None  # None: dùng độ mạnh mặc định của luật
    observed: dict[str, Any]  # giá trị thực tế + ngưỡng, để giải thích


def _pick_tier(value: float, tiers: list[dict]) -> dict | None:
    """Chọn bậc CAO NHẤT mà giá trị đạt tới (không cộng dồn các bậc)."""
    for tier in sorted(tiers, key=lambda t: t["gte"], reverse=True):
        if value >= tier["gte"]:
            return tier
    return None


def count_threshold_tiers(params: dict, features: dict) -> Match | None:
    """Đặc trưng dạng đếm, nhiều bậc. Ví dụ R02: >=3 tài khoản mới/thiết bị: +35; >=5: +50."""
    value = features.get(params["feature"])
    if value is None:
        return None
    tier = _pick_tier(value, params["tiers"])
    if tier is None:
        return None
    return Match(tier["points"], tier.get("strength"), {"value": value, "threshold": tier["gte"]})


def rate_threshold_tiers(params: dict, features: dict) -> Match | None:
    """Tỷ lệ, chỉ xét khi đủ số mẫu tối thiểu. Ví dụ R07: tỷ lệ COD thất bại (đã làm mượt), cần >= 3 đơn."""
    count = features.get(params["count_feature"])
    rate = features.get(params["rate_feature"])
    if count is None or rate is None or count < params.get("min_count", 0):
        return None
    tier = _pick_tier(rate, params["tiers"])
    if tier is None:
        return None
    return Match(tier["points"], tier.get("strength"), {"rate": round(rate, 2), "count": count, "threshold": tier["gte"]})


def compound(params: dict, features: dict) -> Match | None:
    """Nhiều điều kiện cùng đúng (AND). Có thể kèm bậc theo một đặc trưng, ví dụ R08 theo giá trị đơn."""
    observed: dict[str, Any] = {}
    for cond in params["conditions"]:
        value = features.get(cond["feature"])
        if value is None or not OPS[cond["op"]](value, cond["value"]):
            return None
        observed[cond["feature"]] = value
    if "tiers" in params:
        value = features.get(params["tiers"]["feature"])
        tier = _pick_tier(value, params["tiers"]["levels"]) if value is not None else None
        if tier is None:
            return None
        observed |= {"value": value, "threshold": tier["gte"]}
        return Match(tier["points"], tier.get("strength"), observed)
    return Match(params["points"], None, observed)


RULE_TYPES = {
    "count_threshold_tiers": count_threshold_tiers,
    "rate_threshold_tiers": rate_threshold_tiers,
    "compound": compound,
}


def evaluate(rule_type: str, params: dict, features: dict) -> Match | None:
    return RULE_TYPES[rule_type](params, features)


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "?"


def format_reason(template: str, observed: dict[str, Any]) -> str:
    """Điền giá trị vào câu giải thích. Số tiền định dạng kiểu Việt Nam, tỷ lệ thành %."""
    pretty = {}
    for key, value in observed.items():
        if key == "account_age_hours" and isinstance(value, (int, float)) and value < 1:
            pretty[key] = "chưa đầy 1"
        elif isinstance(value, bool):
            pretty[key] = "có" if value else "không"
        elif key == "rate" or (key == "threshold" and isinstance(value, float) and value < 1):
            pretty[key] = f"{value:.0%}"
        elif isinstance(value, int) and abs(value) >= 10_000:
            pretty[key] = f"{value:,}".replace(",", ".")
        elif isinstance(value, float):
            pretty[key] = f"{value:g}"
        else:
            pretty[key] = value
    return template.format_map(_SafeDict(pretty))
