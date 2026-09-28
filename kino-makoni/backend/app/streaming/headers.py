"""Stream/thumb javob sarlavhalari — sof funksiyalar."""

from app.streaming.ranges import ByteRange

DEFAULT_VIDEO_MIME = "video/mp4"
THUMB_CACHE_CONTROL = "public, max-age=604800"
STREAM_CACHE_CONTROL = "private, no-store"


def video_content_type(mime: str | None) -> str:
    """Telegram'dagi mime; bo'sh yoki video bo'lmasa (octet-stream) — video/mp4."""
    value = (mime or "").strip().lower()
    if value.startswith(("video/", "audio/")):
        return value
    return DEFAULT_VIDEO_MIME


def stream_headers(size: int, mime: str | None, byte_range: ByteRange | None) -> dict[str, str]:
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": video_content_type(mime),
        "Cache-Control": STREAM_CACHE_CONTROL,
        "Content-Disposition": "inline",
    }
    if byte_range is None:
        headers["Content-Length"] = str(size)
    else:
        headers["Content-Length"] = str(byte_range.length)
        headers["Content-Range"] = f"bytes {byte_range.start}-{byte_range.end}/{size}"
    return headers


def unsatisfiable_headers(size: int) -> dict[str, str]:
    return {"Accept-Ranges": "bytes", "Content-Range": f"bytes */{size}"}
