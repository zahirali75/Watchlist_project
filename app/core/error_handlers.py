"""Error handler global - satu pintu keluar untuk semua error."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError

logger = logging.getLogger("app.core")


def _error_payload(error_code: int | str, message: str, meta=None) -> dict:
    data: dict = {"errorCode": error_code}
    if meta is not None:
        data["errorMeta"] = meta
    return {"success": False, "message": message, "data": data}


# Kode error untuk HTTP error bawaan framework (rute tidak ada, metode salah, dst.)
# agar bentuknya sama dengan error aplikasi.
_FRAMEWORK_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "Request tidak valid"),
    404: ("NOT_FOUND", "Rute tidak ditemukan"),
    405: ("METHOD_NOT_ALLOWED", "Metode HTTP tidak diizinkan untuk rute ini"),
    406: ("NOT_ACCEPTABLE", "Format respons tidak didukung"),
    413: ("PAYLOAD_TOO_LARGE", "Ukuran request terlalu besar"),
    415: ("UNSUPPORTED_MEDIA_TYPE", "Content-Type tidak didukung"),
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code, default_message = _FRAMEWORK_ERRORS.get(exc.status_code, ("HTTP_ERROR", str(exc.detail)))
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code, default_message),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, exc.meta),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # Dibiarkan 422 (konvensi FastAPI), tapi bentuknya ikut envelope seragam
        # supaya frontend hanya perlu satu cara membaca error.
        return JSONResponse(
            status_code=422,  # UNPROCESSABLE_CONTENT (nama lama: UNPROCESSABLE_ENTITY)
            content=_error_payload(
                "VALIDATION_ERROR",
                "Validasi request gagal",
                [
                    {"location": list(err.get("loc", [])), "message": err.get("msg")}
                    for err in exc.errors()
                ],
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # DICATAT di log server, TIDAK dikirim ke klien.
        logger.exception("Unhandled error pada %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=_error_payload("INTERNAL_ERROR", "Internal Server Error"))
