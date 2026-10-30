"""Cấu hình chung cho test: dùng CSDL riêng riskshop_test, xóa sạch dữ liệu trước mỗi test.

Yêu cầu MariaDB đang chạy và TEST_DATABASE_URL có trong .env.
"""

import argparse
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.db import Base, get_db, make_engine
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]

_url = get_settings().test_database_url
if not _url or "test" not in _url:
    raise RuntimeError("TEST_DATABASE_URL phải trỏ tới CSDL test (tên có chữ 'test') để không xóa nhầm dữ liệu thật")

test_engine = make_engine(_url)
TestSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db():
    # Chạy đúng các migration thật lên CSDL test, nhờ vậy migration cũng được kiểm tra
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.cmd_opts = argparse.Namespace(x=["target=test"])
    command.upgrade(cfg, "head")


@pytest.fixture(autouse=True)
def _clean_tables():
    with test_engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in Base.metadata.sorted_tables:
            conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def _get_test_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _get_test_db


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def db():
    with TestSession() as session:
        yield session
