"""Telethon (MTProto) backend — alohida yordamchi bot sifatida.

Bot kanalni id bo'yicha access_hash'siz "ko'ra olmaydi". Tartib:
1) client.get_input_entity(PeerChannel) — sessiya keshi (SQLite), bo'lmasa Telethon
   o'zi channels.getChannels([InputChannel(id, 0)]) qiladi (bot uchun ruxsat etilgan,
   Pyrogram ham shunday qiladi);
2) topilgan (yoki 0) access_hash bilan channels.getChannels — natija Channel
   bo'lishi shart (ChannelForbidden → bot kanaldan chiqarilgan).
Natija InputPeerChannel sifatida keshlanadi; Telethon uni sessiyaga ham yozadi.
"""

import asyncio
import logging
import random
from collections.abc import AsyncGenerator
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl import functions, types

from app.core.config import Settings
from app.streaming.backend import MediaInfo, ThumbInfo, bare_channel_id
from app.streaming.errors import (
    BackendUnavailable,
    FileRefExpired,
    FloodWait,
    MediaNotFound,
    StreamError,
)

log = logging.getLogger("app.streaming.telegram")

_BACKOFF_START_SEC = 2.0
_BACKOFF_MAX_SEC = 300.0
_SETUP_RETRY_SEC = 120.0  # sozlama xatosida (token/admin) tez-tez urinmaymiz
# Telethon auth-key almashuvida timeout yo'q: TCP ulanib, javob kelmasa abadiy osiladi
CONNECT_TIMEOUT_SEC = 60.0

_FILE_REF_ERRORS = (
    errors.FileReferenceExpiredError,
    errors.FileReferenceInvalidError,
    errors.FilerefUpgradeNeededError,
)
_FLOOD_ERRORS = (errors.FloodWaitError, errors.FloodPremiumWaitError)


class SetupError(Exception):
    """Foydalanuvchi tuzatishi kerak bo'lgan sozlama xatosi (izoh bilan)."""

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.hint = hint


# ---------- xatolar va izohlar ----------


HINT_API_ID = "TG_API_ID / TG_API_HASH noto'g'ri — my.telegram.org → API development tools."
HINT_TOKEN = (
    "TG_HELPER_BOT_TOKEN noto'g'ri yoki bekor qilingan — @BotFather'dan tokenni qayta oling "
    "(asosiy bot tokeni EMAS, alohida yordamchi bot)."
)
HINT_NOT_MEMBER = (
    "Yordamchi bot baza kanalda yo'q — kanal → Administratorlar → botni admin qilib qo'shing."
)
HINT_CHANNEL_ID = (
    "TG_BASE_CHANNEL_ID noto'g'ri yoki bot kanal a'zosi emas — id -100 bilan boshlanadi "
    "(asosiy botdagi BASE_CHANNEL_ID bilan bir xil), yordamchi bot kanalda admin bo'lsin."
)
HINT_SESSION = (
    "Sessiya fayli buzilgan/ikki joyda ishlatilgan — TG_SESSION_DIR'dagi .session faylni o'chiring."
)


def setup_hint(exc: BaseException) -> str | None:
    """Ma'lum sozlama xatolari uchun o'zbekcha maslahat."""
    if isinstance(exc, SetupError):
        return exc.hint or str(exc)
    if isinstance(exc, errors.ApiIdInvalidError):
        return HINT_API_ID
    if isinstance(exc, errors.AccessTokenInvalidError | errors.AccessTokenExpiredError):
        return HINT_TOKEN
    if isinstance(exc, errors.ChannelPrivateError):
        return HINT_NOT_MEMBER
    if isinstance(exc, errors.ChannelInvalidError | errors.PeerIdInvalidError):
        return HINT_CHANNEL_ID
    if isinstance(exc, errors.AuthKeyDuplicatedError):
        return HINT_SESSION
    return None


def to_stream_error(exc: BaseException) -> BaseException:
    """Telethon xatosini stream xatosiga o'giradi (noma'lumi o'zgarishsiz qaytadi)."""
    if isinstance(exc, StreamError):
        return exc
    if isinstance(exc, _FILE_REF_ERRORS):
        return FileRefExpired(str(exc))
    if isinstance(exc, _FLOOD_ERRORS):
        return FloodWait(getattr(exc, "seconds", 0))
    if isinstance(exc, errors.MessageIdInvalidError | errors.MessageIdsEmptyError):
        return MediaNotFound(str(exc))
    if isinstance(
        exc,
        errors.ChannelPrivateError
        | errors.ChannelInvalidError
        | errors.UnauthorizedError
        | errors.ServerError
        | errors.TimedOutError
        | errors.AuthKeyError
        | ConnectionError
        | OSError
        | TimeoutError,
    ):
        return BackendUnavailable(f"{type(exc).__name__}: {exc}")
    if isinstance(exc, errors.RPCError):
        return BackendUnavailable(f"{type(exc).__name__}: {exc}")
    return exc


# ---------- klient, login, kanal ----------


def session_name(bot_token: str, prefix: str = "stream") -> str:
    """Sessiya fayli bot id bo'yicha: token boshqa botga almashsa eski sessiya ishlatilmaydi."""
    bot_id = bot_token.split(":", 1)[0].strip()
    if not bot_id.isdigit():
        raise SetupError(
            "TG_HELPER_BOT_TOKEN formati noto'g'ri",
            "Token '123456:ABC...' ko'rinishida bo'ladi (@BotFather'dan).",
        )
    return f"{prefix}_{bot_id}"


def make_client(settings: Settings, *, name: str, flood_sleep_threshold: int = 0) -> TelegramClient:
    session_dir = Path(settings.tg_session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    return TelegramClient(
        str(session_dir / name),
        settings.tg_api_id,
        settings.tg_api_hash,
        receive_updates=False,  # update'lar kerak emas (InvokeWithoutUpdates)
        flood_sleep_threshold=flood_sleep_threshold,  # 0 — FLOOD_WAIT'ni o'zimiz boshqaramiz
        request_retries=3,
        connection_retries=5,
        retry_delay=2,
        auto_reconnect=True,
        device_model="Kino Makoni API",
        app_version="1.0",
    )


async def login_bot(client: TelegramClient, bot_token: str) -> types.User:
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        await client.sign_in(bot_token=bot_token)
    me = await client.get_me()
    expected_id = int(session_name(bot_token).split("_", 1)[1])
    if me is None or not me.bot:
        raise SetupError(
            "Sessiya bot akkauntiga tegishli emas",
            "TG_SESSION_DIR'dagi eski .session faylni o'chirib qayta ishga tushiring.",
        )
    if me.id != expected_id:
        raise SetupError(
            f"Sessiya boshqa botga tegishli (id {me.id} ≠ {expected_id})",
            "TG_SESSION_DIR'dagi eski .session faylni o'chiring.",
        )
    return me


async def resolve_base_channel(
    client: TelegramClient, channel_id: int
) -> tuple[types.InputPeerChannel, types.Channel]:
    """Baza kanalni bot sifatida aniqlaydi (modul docstring'iga qarang)."""
    try:
        real_id = bare_channel_id(channel_id)
    except ValueError as e:
        raise SetupError(str(e), "TG_BASE_CHANNEL_ID -100... ko'rinishida bo'lsin.") from e

    hashes: list[int] = []
    try:
        cached = await client.get_input_entity(types.PeerChannel(real_id))
        if isinstance(cached, types.InputPeerChannel):
            hashes.append(cached.access_hash)
    except ValueError:
        pass  # keshda yo'q va getChannels(access_hash=0) ham topmadi
    except errors.ChannelPrivateError as e:
        raise SetupError("Bot baza kanalga kira olmaydi", HINT_NOT_MEMBER) from e
    if 0 not in hashes:
        hashes.append(0)

    last_error: Exception | None = None
    for access_hash in hashes:
        try:
            result = await client(
                functions.channels.GetChannelsRequest([types.InputChannel(real_id, access_hash)])
            )
        except (errors.ChannelInvalidError, errors.PeerIdInvalidError) as e:
            last_error = e
            continue
        except errors.ChannelPrivateError as e:
            raise SetupError("Bot baza kanalga kira olmaydi", HINT_NOT_MEMBER) from e
        chat = next((c for c in result.chats if c.id == real_id), None)
        if isinstance(chat, types.ChannelForbidden):
            raise SetupError("Bot baza kanaldan chiqarilgan (ChannelForbidden)", HINT_NOT_MEMBER)
        if isinstance(chat, types.Channel) and chat.access_hash is not None:
            return types.InputPeerChannel(chat.id, chat.access_hash), chat
    raise SetupError(f"Baza kanal {channel_id} topilmadi", HINT_CHANNEL_ID) from last_error


# ---------- xabardan video ----------


def pick_thumb(thumbs: list[types.TypePhotoSize] | None) -> ThumbInfo | None:
    """Eng katta JPEG thumbnail (stripped/path/video thumb'lar hisobga olinmaydi)."""
    best: ThumbInfo | None = None
    best_key = (-1, -1)
    for t in thumbs or []:
        if isinstance(t, types.PhotoSize):
            info = ThumbInfo(t.type, t.size, t.w, t.h)
        elif isinstance(t, types.PhotoSizeProgressive):
            info = ThumbInfo(t.type, max(t.sizes, default=0), t.w, t.h)
        elif isinstance(t, types.PhotoCachedSize):
            info = ThumbInfo(t.type, len(t.bytes), t.w, t.h, inline=bytes(t.bytes))
        else:
            continue
        key = (info.width * info.height, info.size)
        if key > best_key:
            best, best_key = info, key
    return best


def extract_media(message: object) -> MediaInfo | None:
    """Xabardagi video hujjat (DocumentAttributeVideo yoki video/* mime), aks holda None."""
    if message is None or isinstance(message, types.MessageEmpty):
        return None
    media = getattr(message, "media", None)
    if not isinstance(media, types.MessageMediaDocument):
        return None
    doc = media.document
    if not isinstance(doc, types.Document):
        return None
    attrs = doc.attributes or []
    video = next((a for a in attrs if isinstance(a, types.DocumentAttributeVideo)), None)
    mime = (doc.mime_type or "").strip() or None
    if video is None and not (mime or "").lower().startswith("video/"):
        return None
    file_name = next(
        (a.file_name for a in attrs if isinstance(a, types.DocumentAttributeFilename)), None
    )
    return MediaInfo(
        msg_id=message.id,
        doc_id=doc.id,
        access_hash=doc.access_hash,
        file_reference=bytes(doc.file_reference or b""),
        dc_id=doc.dc_id,
        size=int(doc.size),
        mime_type=mime,
        duration=float(video.duration) if video and video.duration is not None else None,
        width=video.w if video else None,
        height=video.h if video else None,
        file_name=file_name,
        supports_streaming=bool(video and video.supports_streaming),
        caption=getattr(message, "message", None) or "",
        thumb=pick_thumb(doc.thumbs),
    )


def document_location(media: MediaInfo, thumb_size: str = "") -> types.InputDocumentFileLocation:
    return types.InputDocumentFileLocation(
        id=media.doc_id,
        access_hash=media.access_hash,
        file_reference=media.file_reference,
        thumb_size=thumb_size,
    )


async def _close_download(it: object) -> None:
    # Telethon limit'ga yetganda close() chaqirmaydi — boshqa DC sender'i shunda qaytadi.
    # Iterator hech boshlanmagan bo'lsa close() AttributeError beradi.
    close = getattr(it, "close", None)
    if close is None:
        return
    try:
        await close()
    except AttributeError:
        pass
    except Exception:
        log.debug("download iterator yopilmadi", exc_info=True)


async def iter_document(
    client: TelegramClient, media: MediaInfo, offset: int, request_size: int, count: int
) -> AsyncGenerator[bytes, None]:
    """upload.getFile bo'laklari (Telethon iter_download: boshqa DC, FILE_MIGRATE ichida)."""
    it = client.iter_download(
        document_location(media),
        offset=offset,
        request_size=request_size,
        chunk_size=request_size,  # stride = chunk_size = request_size → tekislangan so'rovlar
        limit=count,
        file_size=media.size,
        dc_id=media.dc_id,
    )
    try:
        async for chunk in it:
            yield chunk
    except Exception as e:
        mapped = to_stream_error(e)
        if mapped is e:
            raise
        raise mapped from e
    finally:
        await _close_download(it)


# ---------- backend ----------


class TelethonBackend:
    """MediaBackend: fonda ulanadi, uzilsa backoff bilan qayta ulanadi."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: TelegramClient | None = None
        self._channel: types.InputPeerChannel | None = None
        self._ready = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    # ----- hayot sikli -----

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.get_running_loop().create_task(
                self._run(), name="kino-makoni-telegram"
            )

    async def close(self) -> None:
        task, self._task = self._task, None
        if task is not None:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self._drop_client()

    def is_ready(self) -> bool:
        client = self._client
        return (
            self._ready.is_set()
            and self._channel is not None
            and client is not None
            and bool(client.is_connected())
        )

    async def wait_ready(self, wait_sec: float) -> bool:
        if self.is_ready() or self._task is None or self._task.done():
            return self.is_ready()
        try:
            async with asyncio.timeout(wait_sec):
                await self._ready.wait()
        except TimeoutError:
            pass
        return self.is_ready()

    async def _connect(self) -> None:
        s = self._settings
        client = make_client(s, name=session_name(s.tg_helper_bot_token))
        self._client = client
        me = await login_bot(client, s.tg_helper_bot_token)
        channel, chat = await resolve_base_channel(client, s.tg_base_channel_id)
        self._channel = channel
        log.info(
            "Telegram ulandi: @%s, baza kanal %r (dc %s)",
            me.username,
            chat.title,
            client.session.dc_id,
        )

    async def _drop_client(self) -> None:
        self._ready.clear()
        client, self._client, self._channel = self._client, None, None
        if client is None:
            return
        try:
            async with asyncio.timeout(10):
                await client.disconnect()
        except Exception:
            log.debug("Telegram klient uzilmadi", exc_info=True)

    async def _run(self) -> None:
        delay = _BACKOFF_START_SEC
        while True:
            wait = delay
            try:
                async with asyncio.timeout(CONNECT_TIMEOUT_SEC):
                    await self._connect()
            except asyncio.CancelledError:
                raise
            except _FLOOD_ERRORS as e:
                wait = float(getattr(e, "seconds", 0)) + 1
                log.warning("Telegram ulanish FLOOD_WAIT %ss", e.seconds)
            except TimeoutError:
                log.warning(
                    "Telegram %.0f s ichida javob bermadi (tarmoq MTProto'ni to'syaptimi?)",
                    CONNECT_TIMEOUT_SEC,
                )
            except Exception as e:
                hint = setup_hint(e)
                if hint:
                    log.error("Telegram sozlamasi xato: %s — %s", e, hint)
                    wait = max(delay, _SETUP_RETRY_SEC)
                else:
                    log.warning("Telegram'ga ulanib bo'lmadi: %r", e)
                    log.debug("ulanish xatosi tafsiloti", exc_info=True)
            else:
                self._ready.set()
                delay = _BACKOFF_START_SEC
                wait = delay
                client = self._client
                try:
                    if client is not None:
                        await client.disconnected
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    log.warning("Telegram aloqasi uzildi: %r", e)
                else:
                    log.warning("Telegram aloqasi uzildi — qayta ulanamiz")
            await self._drop_client()
            await asyncio.sleep(wait * random.uniform(0.8, 1.2))
            delay = min(delay * 2, _BACKOFF_MAX_SEC)

    # ----- MediaBackend -----

    def _require(self) -> tuple[TelegramClient, types.InputPeerChannel]:
        client, channel = self._client, self._channel
        if client is None or channel is None or not self._ready.is_set():
            raise BackendUnavailable("Telegram ulanmagan")
        return client, channel

    async def fetch_media(self, msg_id: int) -> MediaInfo | None:
        client, channel = self._require()
        try:
            message = await client.get_messages(channel, ids=msg_id)
        except Exception as e:
            mapped = to_stream_error(e)
            if mapped is e:
                raise
            raise mapped from e
        return extract_media(message)

    def iter_chunks(
        self, media: MediaInfo, offset: int, request_size: int, count: int
    ) -> AsyncGenerator[bytes, None]:
        # generatorni to'g'ridan-to'g'ri qaytaramiz: aclose() Telethon iteratorigacha yetadi
        client, _ = self._require()
        return iter_document(client, media, offset, request_size, count)

    async def download_thumb(self, media: MediaInfo) -> bytes | None:
        thumb = media.thumb
        if thumb is None:
            return None
        if thumb.inline is not None:
            return thumb.inline
        client, _ = self._require()
        try:
            data = await client.download_file(
                document_location(media, thumb.type),
                bytes,
                file_size=thumb.size or None,
                dc_id=media.dc_id,
            )
        except Exception as e:
            mapped = to_stream_error(e)
            if mapped is e:
                raise
            raise mapped from e
        return data or None
