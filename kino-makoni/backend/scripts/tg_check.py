#!/usr/bin/env python3
"""Telegram stream sozlamasini tekshirish (backend kodidan foydalanadi).

Backend papkasidan ishga tushiring:

    ./.venv/bin/python scripts/tg_check.py                    # login + kanal
    ./.venv/bin/python scripts/tg_check.py --msg 555          # + xabardagi video
    ./.venv/bin/python scripts/tg_check.py --msg 555 --download-first-mb 16

--msg — bot bazasidagi Movie.baseMsgId / Episode.baseMsgId.
Server bilan to'qnashmaslik uchun alohida sessiya fayli ishlatiladi (check_<bot_id>).
Chiqish kodi: 0 — hammasi joyida, 1 — sozlama xatosi, 2 — Telegram/tarmoq xatosi.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telethon import errors  # noqa: E402

from app.core.config import Settings  # noqa: E402
from app.streaming import telegram as tg  # noqa: E402
from app.streaming.backend import MediaInfo  # noqa: E402
from app.streaming.errors import FileRefExpired, FloodWait, StreamError  # noqa: E402
from app.streaming.ranges import MAX_REQUEST_SIZE  # noqa: E402

MIB = 1024 * 1024
AVPLAYER_MIMES = {"video/mp4", "video/quicktime", "video/x-m4v", "video/mp2t"}


def ok(text: str) -> None:
    print(f"[OK]    {text}")


def warn(text: str) -> None:
    print(f"[DIQQAT] {text}")


def fail(text: str, hint: str | None = None) -> None:
    print(f"[XATO]  {text}")
    if hint:
        print(f"        -> {hint}")


def fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def mp4_top_boxes(data: bytes, limit: int = 12) -> list[str]:
    """Faylning boshidagi yuqori darajadagi MP4 box turlari (ftyp, moov, mdat...)."""
    boxes: list[str] = []
    pos = 0
    while pos + 8 <= len(data) and len(boxes) < limit:
        size = int.from_bytes(data[pos : pos + 4], "big")
        kind = data[pos + 4 : pos + 8].decode("latin-1")
        if not kind.isprintable():
            break
        boxes.append(kind)
        if size == 1 and pos + 16 <= len(data):
            size = int.from_bytes(data[pos + 8 : pos + 16], "big")
        if size < 8:
            break
        pos += size
    return boxes


def check_config(s: Settings) -> bool:
    good = True
    if not s.tg_api_id or not s.tg_api_hash:
        fail("TG_API_ID / TG_API_HASH bo'sh", "my.telegram.org → API development tools")
        good = False
    if not s.tg_helper_bot_token:
        fail(
            "TG_HELPER_BOT_TOKEN bo'sh",
            "@BotFather'da YANGI bot yarating (asosiy bot tokeni emas!)",
        )
        good = False
    if not s.tg_base_channel_id:
        fail("TG_BASE_CHANNEL_ID bo'sh", "asosiy botdagi BASE_CHANNEL_ID (-100...) qiymati")
        good = False
    elif s.tg_base_channel_id > 0 or not str(s.tg_base_channel_id).startswith("-100"):
        warn(f"TG_BASE_CHANNEL_ID={s.tg_base_channel_id} — odatda -100 bilan boshlanadi")
    if good:
        ok(f"Sozlamalar to'ldirilgan (sessiya papkasi: {Path(s.tg_session_dir).resolve()})")
    return good


def print_media(media: MediaInfo) -> None:
    title = next((ln.strip() for ln in reversed(media.caption.splitlines()) if ln.strip()), "-")
    ok(f"Xabar {media.msg_id}: video topildi")
    print(f"        sarlavha : {title}")
    print(f"        fayl     : {media.file_name or '-'}")
    print(f"        hajm     : {media.size / MIB:.1f} MiB ({media.size} bayt)")
    print(f"        mime     : {media.mime_type or '-'}")
    print(f"        davomiyl.: {fmt_duration(media.duration)}")
    print(f"        o'lcham  : {media.width or '?'}x{media.height or '?'}")
    print(f"        DC       : {media.dc_id}")
    streaming = "ha" if media.supports_streaming else "yo'q"
    thumb = f"{media.thumb.type} ({media.thumb.size} bayt)" if media.thumb else "yo'q"
    print(f"        streaming: {streaming}")
    print(f"        thumbnail: {thumb}")
    mime = (media.mime_type or "").lower()
    if mime and mime not in AVPLAYER_MIMES:
        warn(f"{mime} — AVPlayer bu formatni (masalan MKV/WEBM) o'ynay olmaydi; MP4 kerak")
    if media.thumb is None:
        warn("Thumbnail yo'q — /v1/thumb 404 qaytaradi")


async def download_head(client: object, media: MediaInfo, megabytes: float) -> bytes:
    """Faylning boshidan `megabytes` MiB yuklaydi va tezlikni chiqaradi."""
    want = min(max(int(megabytes * MIB), 1), media.size)
    count = (want + MAX_REQUEST_SIZE - 1) // MAX_REQUEST_SIZE
    started = time.perf_counter()
    first_at: float | None = None
    buf = bytearray()
    gen = tg.iter_document(client, media, 0, MAX_REQUEST_SIZE, count)  # type: ignore[arg-type]
    try:
        async for chunk in gen:
            if first_at is None:
                first_at = time.perf_counter() - started
            buf += chunk
    finally:
        await gen.aclose()
    elapsed = max(time.perf_counter() - started, 1e-6)
    ok(
        f"{len(buf) / MIB:.2f} MiB yuklandi: {elapsed:.2f} s, "
        f"{len(buf) / MIB / elapsed:.2f} MiB/s (birinchi bo'lak {first_at or 0:.2f} s)"
    )
    return bytes(buf[:want])


def load_settings(env: str) -> Settings:
    env_file = Path(env)
    if env_file.exists():
        return Settings(_env_file=env_file)
    warn(f"{env_file} topilmadi — faqat muhit o'zgaruvchilari o'qiladi")
    return Settings(_env_file=None)


async def run(settings: Settings, args: argparse.Namespace) -> int:
    if not check_config(settings):
        return 1

    try:
        name = tg.session_name(settings.tg_helper_bot_token, prefix="check")
    except tg.SetupError as e:
        fail(str(e), e.hint)
        return 1

    client = tg.make_client(settings, name=name, flood_sleep_threshold=30)
    try:
        # 1) login
        print(f"Telegram'ga ulanmoqda (DC {client.session.dc_id}, {args.timeout:.0f} s gacha)...")
        try:
            async with asyncio.timeout(args.timeout):
                me = await tg.login_bot(client, settings.tg_helper_bot_token)
        except TimeoutError:
            fail(
                f"Telegram {args.timeout:.0f} s ichida javob bermadi",
                "Tarmoq MTProto'ni to'sayotgan bo'lishi mumkin (firewall/proxy, 443 port).",
            )
            return 2
        except OSError as e:
            fail(f"Telegram'ga ulanib bo'lmadi: {e}", "Tarmoq/firewall: 443 port ochiqmi?")
            return 2
        except Exception as e:
            fail(f"Bot sifatida kirib bo'lmadi: {e!r}", tg.setup_hint(e))
            return 1 if tg.setup_hint(e) else 2
        ok(f"Yordamchi bot: @{me.username} (id {me.id}), DC {client.session.dc_id}")

        # 2) kanal
        try:
            peer, chat = await tg.resolve_base_channel(client, settings.tg_base_channel_id)
        except tg.SetupError as e:
            fail(str(e), e.hint)
            return 1
        except errors.FloodWaitError as e:
            fail(f"Telegram cheklovi: {e.seconds} s kuting")
            return 2
        ok(f"Baza kanal: {chat.title!r} (id {peer.channel_id})")
        if chat.admin_rights is None and not chat.creator:
            warn("Botda admin huquqlari ko'rinmadi — kanalda ADMIN ekanini tekshiring")

        if args.msg is None:
            print("Tayyor. Videoni tekshirish uchun: --msg <baseMsgId>")
            return 0

        # 3) xabar
        try:
            message = await client.get_messages(peer, ids=args.msg)
        except Exception as e:
            fail(f"Xabarni olib bo'lmadi: {e!r}", tg.setup_hint(e))
            return 2
        if message is None:
            fail(f"Xabar {args.msg} topilmadi", "baseMsgId to'g'rimi? Xabar o'chirilmaganmi?")
            return 1
        media = tg.extract_media(message)
        if media is None:
            fail(f"Xabar {args.msg} da video yo'q")
            return 1
        print_media(media)

        # 4) yuklash (birinchi bo'lak doim — getFile/DC ishlashini tekshiradi)
        megabytes = args.download_first_mb or MAX_REQUEST_SIZE / MIB
        try:
            head = await download_head(client, media, megabytes)
        except FloodWait as e:
            fail(f"Telegram cheklovi: {e.seconds} s kuting")
            return 2
        except FileRefExpired:
            fail("file_reference eskirgan — qayta ishga tushiring")
            return 2
        except StreamError as e:
            fail(f"Yuklab bo'lmadi: {e}")
            return 2
        boxes = mp4_top_boxes(head)
        if boxes:
            print(f"        MP4 box'lar: {' → '.join(boxes)}")
            if "moov" in boxes and (
                "mdat" not in boxes or boxes.index("moov") < boxes.index("mdat")
            ):
                ok("moov boshida (faststart) — AVPlayer tez boshlaydi")
            elif "mdat" in boxes:
                warn(
                    "moov fayl oxirida — AVPlayer avval oxirini so'raydi (ishlaydi, start sekinroq)"
                )
            if boxes[0] != "ftyp":
                warn("Fayl ftyp bilan boshlanmaydi — MP4 emas bo'lishi mumkin")
        return 0
    finally:
        await client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description="Kino Makoni: Telegram stream tekshiruvi")
    parser.add_argument("--env", default=str(ROOT / ".env"), help=".env fayl yo'li")
    parser.add_argument("--msg", type=int, help="baza kanaldagi xabar id (baseMsgId)")
    parser.add_argument("--timeout", type=float, default=30, help="ulanish kutish (s)")
    parser.add_argument(
        "--download-first-mb",
        type=float,
        default=0,
        help="faylning boshidan shuncha MiB yuklab tezlikni o'lchash",
    )
    args = parser.parse_args()
    settings = load_settings(args.env)
    try:
        code = asyncio.run(run(settings, args))
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)


if __name__ == "__main__":
    main()
