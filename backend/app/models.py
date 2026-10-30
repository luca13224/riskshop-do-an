"""Nạp model của mọi module vào một chỗ, để Alembic autogenerate nhìn thấy đủ bảng.

Mỗi khi tạo module có models.py mới, thêm một dòng import vào đây.
"""

from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.promotion import models as promotion_models  # noqa: F401
from app.modules.cart import models as cart_models  # noqa: F401
from app.modules.order import models as order_models  # noqa: F401
