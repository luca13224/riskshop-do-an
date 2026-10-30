"""Cấu hình ứng dụng, đọc từ biến môi trường hoặc file .env.

Không bao giờ ghi mật khẩu hay chuỗi kết nối thẳng vào code.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_env: str = "local"
    database_url: str
    test_database_url: str | None = None
    sim_database_url: str | None = None  # CSDL riêng cho bộ mô phỏng (simulator)
    # Danh sách origin cho phép gọi API từ trình duyệt, cách nhau bằng dấu phẩy
    cors_origins: str = "http://localhost:5173"

    # Khóa bí mật để băm IP (HMAC). Đổi khóa thì mọi bản băm IP cũ không so khớp được nữa.
    ip_hash_secret: str
    # Phiên đăng nhập
    session_cookie_name: str = "rs_session"
    session_ttl_hours: int = 24 * 7
    # True khi chạy HTTPS (cookie chỉ gửi qua kết nối mã hóa); local dùng HTTP nên để False
    cookie_secure: bool = False
    # Giới hạn đăng nhập SAI trong một cửa sổ thời gian (chống dò mật khẩu)
    login_window_minutes: int = 15
    login_max_failures_per_account: int = 5
    login_max_failures_per_ip: int = 20

    # Attack Lab: nút "tạo hàng loạt tài khoản giả" KHÔNG được tồn tại trên hệ thống thật,
    # nên mặc định tắt; chỉ bật bằng cấu hình ở môi trường demo.
    demo_mode: bool = False
    lab_api_base: str = "http://127.0.0.1:8000/api"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
