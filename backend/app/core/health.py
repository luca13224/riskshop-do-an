"""Endpoint kiểm tra sức khỏe: API còn sống không, có kết nối được CSDL không."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise AppError("DB_UNAVAILABLE", "Không kết nối được cơ sở dữ liệu.", 503) from exc
    return {"status": "ok", "db": "ok"}
