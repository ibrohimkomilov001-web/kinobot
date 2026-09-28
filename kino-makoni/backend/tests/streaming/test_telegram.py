"""Telethon qatlami: xabardan video ajratish, kanalni aniqlash, xato xaritasi."""

from typing import Any

import pytest
from telethon import errors
from telethon.tl import functions, types

from app.streaming import telegram as tg
from app.streaming.errors import BackendUnavailable, FileRefExpired, FloodWait, MediaNotFound

CHANNEL = -1001234567890
REAL_ID = 1234567890


def make_message(doc: Any, msg_id: int = 55, text: str = "#kino #7\nFilm") -> types.Message:
    return types.Message(
        id=msg_id,
        peer_id=types.PeerChannel(REAL_ID),
        message=text,
        media=types.MessageMediaDocument(document=doc) if doc is not None else None,
    )


def make_doc(**kw: Any) -> types.Document:
    base: dict[str, Any] = {
        "id": 1,
        "access_hash": 2,
        "file_reference": b"ref",
        "date": None,
        "mime_type": "video/mp4",
        "size": 1_500_000_000,
        "dc_id": 4,
        "attributes": [
            types.DocumentAttributeVideo(duration=5400.5, w=1920, h=1080, supports_streaming=True),
            types.DocumentAttributeFilename("film.mp4"),
        ],
        "thumbs": [
            types.PhotoStrippedSize("i", b"\x01\x02"),
            types.PhotoSize("s", 90, 50, 1500),
            types.PhotoSize("m", 320, 180, 9000),
        ],
    }
    base.update(kw)
    return types.Document(**base)


def test_extract_media_video() -> None:
    media = tg.extract_media(make_message(make_doc()))
    assert media is not None
    assert (media.msg_id, media.doc_id, media.access_hash, media.dc_id) == (55, 1, 2, 4)
    assert media.file_reference == b"ref"
    assert media.size == 1_500_000_000
    assert media.mime_type == "video/mp4"
    assert media.duration == 5400.5
    assert (media.width, media.height) == (1920, 1080)
    assert media.file_name == "film.mp4"
    assert media.supports_streaming is True
    assert media.caption.startswith("#kino")
    assert media.thumb is not None and media.thumb.type == "m" and media.thumb.size == 9000


def test_extract_media_mime_only_document() -> None:
    doc = make_doc(mime_type="video/x-matroska", attributes=[], thumbs=None)
    media = tg.extract_media(make_message(doc))
    assert media is not None and media.thumb is None and media.duration is None


@pytest.mark.parametrize(
    "message",
    [
        None,
        types.MessageEmpty(id=5, peer_id=types.PeerChannel(REAL_ID)),
        make_message(None),
        make_message(make_doc(mime_type="application/pdf", attributes=[])),
        make_message(types.DocumentEmpty(id=1)),
    ],
)
def test_extract_media_rejects_non_video(message: Any) -> None:
    assert tg.extract_media(message) is None


def test_pick_thumb_prefers_largest_and_inline() -> None:
    thumbs = [
        types.PhotoSize("m", 320, 180, 9000),
        types.PhotoSizeProgressive("x", 800, 450, [1000, 5000, 20000]),
        types.PhotoCachedSize("s", 90, 50, b"jpeg"),
    ]
    best = tg.pick_thumb(thumbs)
    assert best is not None and best.type == "x" and best.size == 20000
    only_cached = tg.pick_thumb([types.PhotoCachedSize("s", 90, 50, b"jpeg")])
    assert only_cached is not None and only_cached.inline == b"jpeg"
    assert tg.pick_thumb([types.PhotoStrippedSize("i", b"\x01")]) is None
    assert tg.pick_thumb(None) is None


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (errors.FileReferenceExpiredError(None), FileRefExpired),
        (errors.FloodWaitError(None, capture=42), FloodWait),
        (errors.MessageIdInvalidError(None), MediaNotFound),
        (errors.ChannelPrivateError(None), BackendUnavailable),
        (ConnectionError("x"), BackendUnavailable),
        (errors.RPCError(None, "WEIRD_ERROR", 400), BackendUnavailable),
    ],
)
def test_to_stream_error(exc: BaseException, expected: type) -> None:
    mapped = tg.to_stream_error(exc)
    assert isinstance(mapped, expected)
    if isinstance(mapped, FloodWait):
        assert mapped.seconds == 42


def test_to_stream_error_keeps_unknown() -> None:
    exc = KeyError("x")
    assert tg.to_stream_error(exc) is exc


def test_session_name_and_hints() -> None:
    assert tg.session_name("123456:ABC") == "stream_123456"
    assert tg.session_name("123456:ABC", prefix="check") == "check_123456"
    with pytest.raises(tg.SetupError):
        tg.session_name("not-a-token")
    assert tg.setup_hint(errors.ApiIdInvalidError(None)) == tg.HINT_API_ID
    assert tg.setup_hint(errors.AccessTokenInvalidError(None)) == tg.HINT_TOKEN
    assert tg.setup_hint(errors.ChannelPrivateError(None)) == tg.HINT_NOT_MEMBER
    assert tg.setup_hint(ValueError("x")) is None


class FakeTgClient:
    """resolve_base_channel uchun minimal Telethon klient."""

    def __init__(
        self,
        *,
        cached_hash: int | None = None,
        real_hash: int = 777,
        private: bool = False,
        forbidden: bool = False,
        member: bool = True,
    ) -> None:
        self.cached_hash = cached_hash
        self.real_hash = real_hash
        self.private = private
        self.forbidden = forbidden
        self.member = member
        self.calls: list[int] = []

    async def get_input_entity(self, peer: types.PeerChannel) -> Any:
        if self.cached_hash is not None:
            return types.InputPeerChannel(peer.channel_id, self.cached_hash)
        raise ValueError("not cached")

    async def __call__(self, request: Any) -> Any:
        assert isinstance(request, functions.channels.GetChannelsRequest)
        (inp,) = request.id
        self.calls.append(inp.access_hash)
        if self.private:
            raise errors.ChannelPrivateError(request)
        if not self.member or inp.access_hash not in (0, self.real_hash):
            raise errors.ChannelInvalidError(request)
        if self.forbidden:
            chat: Any = types.ChannelForbidden(inp.channel_id, self.real_hash, "Base")
        else:
            chat = types.Channel(
                id=inp.channel_id,
                title="Base",
                photo=types.ChatPhotoEmpty(),
                date=None,
                access_hash=self.real_hash,
                broadcast=True,
            )
        return types.messages.Chats(chats=[chat])


async def test_resolve_channel_with_access_hash_zero() -> None:
    client = FakeTgClient()
    peer, chat = await tg.resolve_base_channel(client, CHANNEL)  # type: ignore[arg-type]
    assert peer == types.InputPeerChannel(REAL_ID, 777)
    assert chat.title == "Base"
    assert client.calls == [0]


async def test_resolve_channel_uses_cached_hash() -> None:
    client = FakeTgClient(cached_hash=777)
    peer, _ = await tg.resolve_base_channel(client, CHANNEL)  # type: ignore[arg-type]
    assert peer.access_hash == 777
    assert client.calls == [777]


async def test_resolve_channel_stale_cached_hash_falls_back() -> None:
    client = FakeTgClient(cached_hash=111)
    peer, _ = await tg.resolve_base_channel(client, CHANNEL)  # type: ignore[arg-type]
    assert peer.access_hash == 777
    assert client.calls == [111, 0]


@pytest.mark.parametrize(
    ("kw", "hint"),
    [
        ({"private": True}, tg.HINT_NOT_MEMBER),
        ({"forbidden": True}, tg.HINT_NOT_MEMBER),
        ({"member": False}, tg.HINT_CHANNEL_ID),
    ],
)
async def test_resolve_channel_errors(kw: dict[str, Any], hint: str) -> None:
    with pytest.raises(tg.SetupError) as exc:
        await tg.resolve_base_channel(FakeTgClient(**kw), CHANNEL)  # type: ignore[arg-type]
    assert exc.value.hint == hint


async def test_resolve_channel_rejects_group_id() -> None:
    with pytest.raises(tg.SetupError):
        await tg.resolve_base_channel(FakeTgClient(), -123456)  # type: ignore[arg-type]


class FakeDownloadIter:
    """Telethon RequestIter o'xshashi: limit'da o'zi close() qilmaydi."""

    def __init__(self, chunks: list[bytes], fail: BaseException | None = None) -> None:
        self.chunks = list(chunks)
        self.fail = fail
        self.closed = 0
        self.started = False

    def __aiter__(self) -> "FakeDownloadIter":
        return self

    async def __anext__(self) -> bytes:
        self.started = True
        if self.fail is not None:
            raise self.fail
        if not self.chunks:
            raise StopAsyncIteration
        return self.chunks.pop(0)

    async def close(self) -> None:
        if not self.started:
            raise AttributeError("_sender")  # Telethon: boshlanmagan iterator
        self.closed += 1


class FakeDownloadClient:
    def __init__(self, it: FakeDownloadIter) -> None:
        self.it = it
        self.kwargs: dict[str, Any] = {}

    def iter_download(self, location: Any, **kwargs: Any) -> FakeDownloadIter:
        self.kwargs = kwargs
        self.location = location
        return self.it


async def test_iter_document_params_and_close() -> None:
    media = tg.extract_media(make_message(make_doc()))
    assert media is not None
    it = FakeDownloadIter([b"a", b"b", b"c"])
    client = FakeDownloadClient(it)
    gen = tg.iter_document(client, media, 1024 * 1024, 512 * 1024, 3)  # type: ignore[arg-type]
    assert await anext(gen) == b"a"
    await gen.aclose()  # mijoz uzildi
    assert it.closed == 1
    assert client.kwargs == {
        "offset": 1024 * 1024,
        "request_size": 512 * 1024,
        "chunk_size": 512 * 1024,
        "limit": 3,
        "file_size": media.size,
        "dc_id": 4,
    }
    assert isinstance(client.location, types.InputDocumentFileLocation)
    assert client.location.thumb_size == ""


async def test_iter_document_maps_errors() -> None:
    media = tg.extract_media(make_message(make_doc()))
    assert media is not None
    it = FakeDownloadIter([], fail=errors.FileReferenceExpiredError(None))
    gen = tg.iter_document(FakeDownloadClient(it), media, 0, 4096, 1)  # type: ignore[arg-type]
    with pytest.raises(FileRefExpired):
        await anext(gen)
    assert it.closed == 1


async def test_close_download_unstarted_is_safe() -> None:
    it = FakeDownloadIter([b"x"])
    await tg._close_download(it)  # Telethon'da boshlanmagan iterator AttributeError beradi
    assert it.closed == 0
    await tg._close_download(object())  # close() yo'q
