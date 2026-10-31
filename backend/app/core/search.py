"""Tiện ích tìm kiếm văn bản dùng chung."""

# Ký tự escape dùng với LIKE: truyền vào `.like(pattern, escape=LIKE_ESCAPE)`
LIKE_ESCAPE = "\\"


def contains_pattern(q: str) -> str:
    """Mẫu LIKE "chứa chuỗi q". Escape %, _ và dấu gạch chéo ngược để người dùng không chèn được ký tự
    đại diện của LIKE. Collation utf8mb4_unicode_ci nên không phân biệt hoa thường."""
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
