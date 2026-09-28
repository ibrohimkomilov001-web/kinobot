"""/v1/stream va /v1/thumb endpointlari (docs/API.md → "Ijro (playback)")."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

from app.core import signing
from app.streaming import service
from app.streaming.errors import Busy, FloodWait, MediaNotFound, StreamBroken, StreamError
from app.streaming.headers import THUMB_CACHE_CONTROL, stream_headers, unsatisfiable_headers
from app.streaming.ranges import ByteRange, RangeNotSatisfiable, parse_range_header
from app.streaming.streamer import ByteStream, Streamer

log = logging.getLogger("app.streaming")

router = APIRouter(tags=["stream"])

MSG_FORBIDDEN = "Havola eskirgan yoki yaroqsiz"
MSG_WRONG_SOURCE = "Bu manbaga ruxsat yo'q"
MSG_UNAVAILABLE = "Telegram ulanmagan"
MSG_BROKEN = "Videoni Telegram'dan o'qib bo'lmadi"
MSG_VIDEO_NOT_FOUND = "Video topilmadi"
MSG_THUMB_NOT_FOUND = "Rasm topilmadi"
MSG_FLOOD = "Telegram cheklovi — birozdan keyin urinib ko'ring"
MSG_BUSY = "Server band — birozdan keyin urinib ko'ring"
MSG_RANGE = "So'ralgan bayt oralig'i noto'g'ri"


def _error(
    status: int, code: str, message: str, headers: dict[str, str] | None = None
) -> HTTPException:
    return HTTPException(status, detail={"code": code, "message": message}, headers=headers)


def _http_error(exc: StreamError, not_found_message: str) -> HTTPException:
    if isinstance(exc, MediaNotFound):
        return _error(404, "not_found", not_found_message)
    if isinstance(exc, FloodWait):
        return _error(503, "rate_limited", MSG_FLOOD, {"Retry-After": str(max(exc.seconds, 1))})
    if isinstance(exc, Busy):
        return _error(503, "rate_limited", MSG_BUSY, {"Retry-After": "5"})
    if isinstance(exc, StreamBroken):
        return _error(503, "unavailable", MSG_BROKEN)
    return _error(503, "unavailable", MSG_UNAVAILABLE)


def _verify(token: str, src: str) -> tuple[int, int]:
    """Imzolangan token → (ch, msg). Har qanday nuqson → 403."""
    try:
        payload: dict[str, Any] = signing.verify(token)
    except signing.InvalidToken:
        raise _error(403, "forbidden", MSG_FORBIDDEN) from None
    ch, msg = payload.get("ch"), payload.get("msg")
    if (
        payload.get("v") != 1
        or payload.get("src") != src
        or not isinstance(ch, int)
        or not isinstance(msg, int)
        or isinstance(ch, bool)
        or isinstance(msg, bool)
        or msg <= 0
    ):
        raise _error(403, "forbidden", MSG_FORBIDDEN)
    return ch, msg


def _streamer_for(channel_id: int) -> Streamer:
    streamer = service.current()
    if streamer is None:
        raise _error(503, "unavailable", MSG_UNAVAILABLE)
    if not streamer.accepts_channel(channel_id):
        raise _error(403, "forbidden", MSG_WRONG_SOURCE)
    return streamer


class TelegramStreamResponse(StreamingResponse):
    """StreamingResponse + kafolatlangan tozalash: mijoz uzilsa ham, javob
    boshlanmasdan bekor qilinsa ham Telegram yuklashi darhol to'xtaydi."""

    def __init__(self, stream: ByteStream, status_code: int, headers: dict[str, str]) -> None:
        super().__init__(stream, status_code=status_code, headers=headers)
        self._stream = stream

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            await self._stream.aclose()


@router.api_route("/v1/stream/{token}/{filename}", methods=["GET", "HEAD"])
async def stream_video(request: Request, token: str, filename: str) -> Response:
    ch, msg = _verify(token, "tg")
    streamer = _streamer_for(ch)
    try:
        media = await streamer.get_media(msg)
    except StreamError as e:
        raise _http_error(e, MSG_VIDEO_NOT_FOUND) from None

    size = media.size
    try:
        byte_range = parse_range_header(request.headers.get("range"), size)
    except RangeNotSatisfiable:
        raise _error(416, "range_not_satisfiable", MSG_RANGE, unsatisfiable_headers(size)) from None

    status = 200 if byte_range is None else 206
    headers = stream_headers(size, media.mime_type, byte_range)
    if request.method == "HEAD" or size == 0:
        return Response(status_code=status, headers=headers)

    stream = streamer.open_stream(msg, media, byte_range or ByteRange(0, size - 1))
    try:
        await stream.prefetch()
    except StreamError as e:
        await stream.aclose()
        log.warning("stream msg=%s boshlanmadi: %r", msg, e)
        raise _http_error(e, MSG_VIDEO_NOT_FOUND) from None
    except BaseException:
        await stream.aclose()
        raise
    return TelegramStreamResponse(stream, status, headers)


@router.get("/v1/thumb/{token}/poster.jpg")
async def video_thumb(token: str) -> Response:
    ch, msg = _verify(token, "tg-thumb")
    streamer = _streamer_for(ch)
    try:
        data = await streamer.get_thumb(ch, msg)
    except StreamError as e:
        raise _http_error(e, MSG_THUMB_NOT_FOUND) from None
    return Response(
        content=data, media_type="image/jpeg", headers={"Cache-Control": THUMB_CACHE_CONTROL}
    )
