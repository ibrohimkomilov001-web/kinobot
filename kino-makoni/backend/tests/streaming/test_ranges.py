import pytest

from app.streaming.backend import bare_channel_id, marked_channel_id
from app.streaming.headers import stream_headers, unsatisfiable_headers, video_content_type
from app.streaming.ranges import (
    ByteRange,
    RangeNotSatisfiable,
    normalize_request_size,
    parse_range_header,
)

SIZE = 1000


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("bytes=0-0", ByteRange(0, 0)),
        ("bytes=0-1", ByteRange(0, 1)),
        ("bytes=0-999", ByteRange(0, 999)),
        ("bytes=0-", ByteRange(0, 999)),
        ("bytes=500-", ByteRange(500, 999)),
        ("bytes=999-", ByteRange(999, 999)),
        ("bytes=100-199", ByteRange(100, 199)),
        ("bytes=900-5000", ByteRange(900, 999)),  # oxiri hajmga qisqaradi
        ("bytes=-1", ByteRange(999, 999)),
        ("bytes=-500", ByteRange(500, 999)),
        ("bytes=-1000", ByteRange(0, 999)),
        ("bytes=-99999", ByteRange(0, 999)),  # suffix hajmdan katta → butun fayl
        ("BYTES=10-20", ByteRange(10, 20)),
        ("bytes= 10-20 ", ByteRange(10, 20)),
        ("bytes=10-20,30-40", ByteRange(10, 20)),  # multi-range → birinchisi
        ("bytes=5000-6000, 10-20", ByteRange(10, 20)),  # birinchi qanoatlantiriladigani
        ("bytes=10-20,,", ByteRange(10, 20)),
        ("items=0-10", None),  # noma'lum birlik e'tiborsiz (RFC 9110)
    ],
)
def test_parse_range_ok(header: str | None, expected: ByteRange | None) -> None:
    assert parse_range_header(header, SIZE) == expected


@pytest.mark.parametrize(
    "header",
    [
        "bytes=1000-",  # boshi = hajm
        "bytes=1000-2000",
        "bytes=5000-6000,7000-",
        "bytes=-0",
        "bytes=20-10",  # end < start
        "bytes=abc",
        "bytes=a-b",
        "bytes=1-x",
        "bytes=-x",
        "bytes=--5",
        "bytes=+1-5",
        "bytes=",
        "bytes=,",
        "bytes",
        "bytes=0-1,zz",  # keyingi qismda sintaksis xatosi
        "bytes=١-٢",  # ASCII bo'lmagan raqamlar
    ],
)
def test_parse_range_unsatisfiable(header: str) -> None:
    with pytest.raises(RangeNotSatisfiable) as exc:
        parse_range_header(header, SIZE)
    assert exc.value.size == SIZE


def test_parse_range_empty_file() -> None:
    assert parse_range_header(None, 0) is None
    for header in ("bytes=0-", "bytes=-5", "bytes=0-0"):
        with pytest.raises(RangeNotSatisfiable):
            parse_range_header(header, 0)


def test_byte_range_length() -> None:
    assert ByteRange(0, 0).length == 1
    assert ByteRange(10, 19).length == 10


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (512 * 1024, 512 * 1024),
        (1024 * 1024, 512 * 1024),  # Telethon/MTProto maksimumi
        (300_000, 256 * 1024),
        (4096, 4096),
        (5000, 4096),
        (1000, 4096),
        (0, 4096),
        (-5, 4096),
        (128 * 1024 + 1, 128 * 1024),
    ],
)
def test_normalize_request_size(value: int, expected: int) -> None:
    got = normalize_request_size(value)
    assert got == expected
    assert got % 4096 == 0 and (1024 * 1024) % got == 0


def test_stream_headers_full_and_partial() -> None:
    full = stream_headers(1000, "video/mp4", None)
    assert full == {
        "Accept-Ranges": "bytes",
        "Content-Type": "video/mp4",
        "Cache-Control": "private, no-store",
        "Content-Disposition": "inline",
        "Content-Length": "1000",
    }
    part = stream_headers(1000, "video/quicktime", ByteRange(10, 19))
    assert part["Content-Length"] == "10"
    assert part["Content-Range"] == "bytes 10-19/1000"
    assert part["Content-Type"] == "video/quicktime"
    assert unsatisfiable_headers(1000) == {
        "Accept-Ranges": "bytes",
        "Content-Range": "bytes */1000",
    }


@pytest.mark.parametrize(
    ("mime", "expected"),
    [
        (None, "video/mp4"),
        ("", "video/mp4"),
        ("application/octet-stream", "video/mp4"),
        ("video/x-matroska", "video/x-matroska"),
        ("Video/MP4", "video/mp4"),
    ],
)
def test_video_content_type(mime: str | None, expected: str) -> None:
    assert video_content_type(mime) == expected


def test_channel_id_helpers() -> None:
    assert marked_channel_id(-1001234567890) == -1001234567890
    assert marked_channel_id(1234567890) == -1001234567890
    assert bare_channel_id(-1001234567890) == 1234567890
    assert bare_channel_id(1234567890) == 1234567890
    with pytest.raises(ValueError):
        bare_channel_id(-123456)  # oddiy guruh, kanal emas
