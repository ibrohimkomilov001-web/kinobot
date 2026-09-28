import httpx
import pytest

from app.streaming import service
from app.streaming.streamer import Streamer
from tests.streaming.conftest import CHANNEL, CHUNK, stream_token, thumb_token
from tests.streaming.fakes import FakeBackend, pattern_bytes

SIZE = 3 * CHUNK + 12345
DATA = pattern_bytes(SIZE, seed=3)
JPEG = b"\xff\xd8\xff\xe0fake-jpeg\xff\xd9"


@pytest.fixture(autouse=True)
def _files(backend: FakeBackend) -> None:
    backend.add(5, DATA, thumb=JPEG)
    backend.add(6, b"x" * 100, mime=None)  # thumb yo'q, mime yo'q


def url(msg: int = 5, **kw: object) -> str:
    return f"/v1/stream/{stream_token(msg, **kw)}/video.mp4"  # type: ignore[arg-type]


def assert_common(resp: httpx.Response) -> None:
    assert resp.headers["accept-ranges"] == "bytes"
    assert resp.headers["cache-control"] == "private, no-store"
    assert resp.headers["content-disposition"] == "inline"
    assert resp.headers["content-type"] == "video/mp4"


def error_code(resp: httpx.Response) -> str:
    # backend-core handler {"error": ...} ga o'giradi; bu yerda FastAPI standart {"detail": ...}
    return resp.json()["detail"]["code"]


async def test_full_200(client: httpx.AsyncClient) -> None:
    resp = await client.get(url())
    assert resp.status_code == 200
    assert resp.content == DATA
    assert resp.headers["content-length"] == str(SIZE)
    assert "content-range" not in resp.headers
    assert_common(resp)


async def test_partial_206(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    start, end = CHUNK - 10, 2 * CHUNK + 5  # uchta bo'lakni kesib o'tadi
    resp = await client.get(url(), headers={"Range": f"bytes={start}-{end}"})
    assert resp.status_code == 206
    assert resp.content == DATA[start : end + 1]
    assert resp.headers["content-length"] == str(end - start + 1)
    assert resp.headers["content-range"] == f"bytes {start}-{end}/{SIZE}"
    assert_common(resp)
    assert [off for off, _ in backend.requests] == [0, CHUNK, 2 * CHUNK]


async def test_probe_two_bytes(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(), headers={"Range": "bytes=0-1"})
    assert resp.status_code == 206
    assert resp.content == DATA[:2]
    assert resp.headers["content-range"] == f"bytes 0-1/{SIZE}"


async def test_open_ended_range(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(), headers={"Range": f"bytes={SIZE - 7}-"})
    assert resp.status_code == 206
    assert resp.content == DATA[-7:]


async def test_suffix_range(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(), headers={"Range": "bytes=-500"})
    assert resp.status_code == 206
    assert resp.content == DATA[-500:]
    assert resp.headers["content-range"] == f"bytes {SIZE - 500}-{SIZE - 1}/{SIZE}"


async def test_multi_range_serves_first(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(), headers={"Range": "bytes=10-19,100-200"})
    assert resp.status_code == 206
    assert resp.content == DATA[10:20]


@pytest.mark.parametrize("header", [f"bytes={SIZE}-", "bytes=-0", "bytes=9-3", "bytes=x-y"])
async def test_416(client: httpx.AsyncClient, backend: FakeBackend, header: str) -> None:
    resp = await client.get(url(), headers={"Range": header})
    assert resp.status_code == 416
    assert resp.headers["content-range"] == f"bytes */{SIZE}"
    assert error_code(resp) == "range_not_satisfiable"
    assert backend.requests == []


async def test_head_full_and_range(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    resp = await client.head(url())
    assert resp.status_code == 200
    assert resp.content == b""
    assert resp.headers["content-length"] == str(SIZE)
    assert_common(resp)

    resp = await client.head(url(), headers={"Range": "bytes=100-"})
    assert resp.status_code == 206
    assert resp.content == b""
    assert resp.headers["content-length"] == str(SIZE - 100)
    assert resp.headers["content-range"] == f"bytes 100-{SIZE - 1}/{SIZE}"
    assert backend.requests == []  # HEAD Telegram'dan fayl yuklamaydi


async def test_missing_mime_defaults_to_mp4(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(6))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "video/mp4"
    assert resp.content == b"x" * 100


async def test_metadata_cached(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    for _ in range(3):
        assert (await client.head(url())).status_code == 200
    assert backend.fetch_calls == 1


async def test_expired_token_403(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(ttl=-10))
    assert resp.status_code == 403
    assert error_code(resp) == "forbidden"


@pytest.mark.parametrize(
    "token",
    [
        "garbage",
        "a.b",
        stream_token(5) + "x",  # imzo buzilgan
    ],
)
async def test_invalid_token_403(client: httpx.AsyncClient, token: str) -> None:
    resp = await client.get(f"/v1/stream/{token}/video.mp4")
    assert resp.status_code == 403
    assert error_code(resp) == "forbidden"


async def test_wrong_src_403(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(src="tg-thumb"))
    assert resp.status_code == 403
    resp = await client.get(f"/v1/thumb/{thumb_token(5, src='tg')}/poster.jpg")
    assert resp.status_code == 403


async def test_wrong_channel_403(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    resp = await client.get(url(ch=-1009999999999))
    assert resp.status_code == 403
    assert error_code(resp) == "forbidden"
    assert backend.fetch_calls == 0
    resp = await client.get(f"/v1/thumb/{thumb_token(5, ch=-1009999999999)}/poster.jpg")
    assert resp.status_code == 403


async def test_bare_channel_id_accepted(client: httpx.AsyncClient) -> None:
    resp = await client.head(url(ch=1234567890))  # -100 siz yozilgan xuddi shu kanal
    assert resp.status_code == 200
    assert CHANNEL == -1001234567890


async def test_not_found_404(client: httpx.AsyncClient) -> None:
    resp = await client.get(url(404))
    assert resp.status_code == 404
    assert error_code(resp) == "not_found"
    assert resp.json()["detail"]["message"] == "Video topilmadi"


async def test_telegram_disabled_503(client: httpx.AsyncClient) -> None:
    service.install(None)
    resp = await client.get(url())
    assert resp.status_code == 503
    assert error_code(resp) == "unavailable"
    assert resp.json()["detail"]["message"] == "Telegram ulanmagan"
    resp = await client.get(f"/v1/thumb/{thumb_token(5)}/poster.jpg")
    assert resp.status_code == 503


async def test_backend_not_ready_503(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    backend.ready = False
    resp = await client.get(url())
    assert resp.status_code == 503
    assert error_code(resp) == "unavailable"


async def test_long_flood_wait_503(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    backend.flood_once = 120
    resp = await client.get(url(), headers={"Range": "bytes=0-1"})
    assert resp.status_code == 503
    assert error_code(resp) == "rate_limited"
    assert resp.headers["retry-after"] == "120"
    assert backend.open_iterators == 0


async def test_long_flood_on_metadata_503(client: httpx.AsyncClient, backend: FakeBackend) -> None:
    backend.flood_on_fetch = 300
    resp = await client.get(url())
    assert resp.status_code == 503
    assert error_code(resp) == "rate_limited"


async def test_backend_error_on_first_chunk_503(
    client: httpx.AsyncClient, backend: FakeBackend
) -> None:
    backend.fail_unavailable = True
    resp = await client.get(url())
    assert resp.status_code == 503
    assert error_code(resp) == "unavailable"
    assert backend.open_iterators == 0


async def test_thumb_200_and_cached(
    client: httpx.AsyncClient, backend: FakeBackend, streamer: Streamer
) -> None:
    resp = await client.get(f"/v1/thumb/{thumb_token(5)}/poster.jpg")
    assert resp.status_code == 200
    assert resp.content == JPEG
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.headers["cache-control"] == "public, max-age=604800"

    path = streamer.thumb_path(CHANNEL, 5)
    assert path is not None and path.read_bytes() == JPEG
    assert path.name == f"{CHANNEL}_5.jpg"

    resp = await client.get(f"/v1/thumb/{thumb_token(5)}/poster.jpg")
    assert resp.status_code == 200
    assert backend.thumb_calls == 1


async def test_thumb_served_from_disk_when_disconnected(
    client: httpx.AsyncClient, backend: FakeBackend, streamer: Streamer
) -> None:
    path = streamer.thumb_path(CHANNEL, 77)
    assert path is not None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(JPEG)
    backend.ready = False
    resp = await client.get(f"/v1/thumb/{thumb_token(77)}/poster.jpg")
    assert resp.status_code == 200
    assert resp.content == JPEG


async def test_thumb_404(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"/v1/thumb/{thumb_token(6)}/poster.jpg")
    assert resp.status_code == 404
    assert error_code(resp) == "not_found"
    assert resp.json()["detail"]["message"] == "Rasm topilmadi"
    resp = await client.get(f"/v1/thumb/{thumb_token(999)}/poster.jpg")
    assert resp.status_code == 404
