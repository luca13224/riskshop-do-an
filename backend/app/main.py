"""Điểm vào của backend.

Chạy (trong thư mục backend, đã kích hoạt .venv):
    uvicorn app.main:app --reload --port 8000
Tài liệu API tự sinh: http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import errors, health
from app.core.config import get_settings
from app.modules.auth.deps import DEVICE_HEADER
from app.modules.auth.router import router as auth_router
from app.modules.cart.router import router as cart_router
from app.modules.cases.router import router as cases_router
from app.modules.catalog.router import router as catalog_router
from app.modules.lab.router import router as lab_router
from app.modules.order.router import router as order_router
from app.modules.reports.router import router as reports_router
from app.modules.risk.router import router as risk_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RiskShop API", version="0.1.0")

    # CORS: cho phép frontend (Vite, cổng 5173) gọi API từ trình duyệt
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Idempotency-Key", DEVICE_HEADER, errors.REQUEST_ID_HEADER],
        expose_headers=[errors.REQUEST_ID_HEADER],
    )
    errors.install(app)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(catalog_router, prefix="/api")
    app.include_router(cart_router, prefix="/api")
    app.include_router(order_router, prefix="/api")
    app.include_router(risk_router, prefix="/api")
    app.include_router(cases_router, prefix="/api")
    app.include_router(lab_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    return app


app = create_app()
