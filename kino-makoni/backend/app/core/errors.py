"""Xato javoblari — docs/API.md kontraktiga mos yagona shakl.

Har doim: {"error": {"code": ..., "message": ...}}. `raise_error` o'z endpoint
kodimizda ishlatiladi; `http_exception_handler` esa BOSHQA joyda (masalan
streaming moduli) ko'tarilgan HTTPException'larni ham shu shaklga o'tkazadi.
"""

from __future__ import annotations

import logging
from typing import NoReturn

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("kino_makoni")

# HTTP status → standart xato kodi (detail'da kod berilmagan hollar uchun)
_STATUS_DEFAULT_CODE: dict[int, str] = {
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "unavailable",
    416: "range_not_satisfiable",
    422: "validation_error",
    429: "rate_limited",
    503: "unavailable",
    500: "internal",
}


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def raise_error(status_code: int, code: str, message: str) -> NoReturn:
    """Kontraktga mos xato ko'tarish — detail doim {"code","message"} dict."""
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        code, message = str(detail["code"]), str(detail["message"])
    else:
        code = _STATUS_DEFAULT_CODE.get(exc.status_code, "internal")
        message = detail if isinstance(detail, str) and detail else code
    response = JSONResponse(status_code=exc.status_code, content=error_body(code, message))
    # streaming moduli 416'da Content-Range beradi — headerlarni saqlab qolamiz
    if exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "So'rov ma'lumotlari noto'g'ri"),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Kutilmagan xato: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content=error_body("internal", "Ichki server xatosi"))
