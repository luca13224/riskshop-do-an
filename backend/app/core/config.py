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
    # Danh sách origin cho phép gọi API từ trình duyệt, cách nhau bằng dấu phẩy
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
