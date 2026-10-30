"""Định dạng lỗi thống nhất cho toàn bộ API.

Mọi lỗi trả về client có dạng:
    {"error": {"code": "...", "message": "...", "request_id": "..."}}

Lỗi không lường trước (bug) chỉ trả thông điệp chung; chi tiết nằm trong log, không lộ ra ngoài.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("app")

REQUEST_ID_HEADER = "X-Request-ID"


class AppError(Exception):
    """Lỗi nghiệp vụ có chủ đích, ví dụ AppError("VOUCHER_EXPIRED", "Mã đã hết hạn", 409)."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _error_response(request: Request, status_code: int, code: str, message: str, **extra) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "request_id": request.state.request_id, **extra}}
    return JSONResponse(status_code=status_code, content=body)


def install(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        # Mỗi request có một mã riêng để lần theo trong log, trong lỗi và trong quyết định rủi ro
        request.state.request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request.state.request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return _error_response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(p) for p in e["loc"] if p != "body"), "message": e["msg"]}
            for e in exc.errors()
        ]
        return _error_response(request, 422, "VALIDATION_ERROR", "Dữ liệu gửi lên không hợp lệ.", fields=fields)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
            exc.status_code, "HTTP_ERROR"
        )
        return _error_response(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        log.exception("Unhandled error request_id=%s", request.state.request_id)
        return _error_response(request, 500, "INTERNAL_ERROR", "Hệ thống gặp lỗi, vui lòng thử lại sau.")
