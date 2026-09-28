"""Umumiy matn tozalash yordamchilari — emoji va HTML bilan ishlash.

`catalog_sync.py` ikki joyda ishlatadi: janr matnini tozalashda (emoji/#
olib tashlash) va caption'dan tavsif chiqarishda (emoji-only qatorlarni
aniqlashda).
"""

from __future__ import annotations

import html
import re

# Keng tarqalgan emoji diapazonlari (piktogramma, belgi, bayroq, ZWJ/variatsiya)
EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001faff"
    "\U00002600-\U000027bf"
    "\U0001f1e6-\U0001f1ff"
    "\U00002190-\U000021ff"
    "\U00002b00-\U00002bff"
    "\U0000fe0f"
    "\U0000200d"
    "]",
    flags=re.UNICODE,
)

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """HTML teglarini olib tashlaydi va entitylarni (&amp; kabi) ochadi."""
    return html.unescape(_TAG_RE.sub(" ", text))


def strip_emoji(text: str) -> str:
    return EMOJI_RE.sub("", text)


def is_emoji_only(line: str) -> bool:
    """Qator faqat emoji/tinish belgilaridan iboratmi (matn harf/raqamsiz)."""
    stripped = EMOJI_RE.sub("", line)
    stripped = re.sub(r"[\s•\-–—.,!?:;]+", "", stripped)
    return stripped == ""


_URL_RE = re.compile(r"(https?://\S+|t\.me/\S+|www\.\S+)", re.IGNORECASE)
_MENTION_LINE_RE = re.compile(r"^(@[\w\d_]+[\s,]*)+$", re.UNICODE)
_CODE_LINE_RE = re.compile(r"^(#\S+\s*)+$")
_LABEL_RE = re.compile(
    r"^(janr(i|lar)?|sifat(i)?|til(i)?|davomiylig?i|nomi|kodi?|yil(i)?|"
    r"genre|quality|language|duration)\s*[:\-—]",
    re.IGNORECASE | re.UNICODE,
)


def extract_description(caption: str | None) -> str | None:
    """Bot caption'idan tabiiy tavsif matnini ajratib oladi.

    Olib tashlanadi: HTML teglari/entity'lar, faqat link/mention bo'lgan
    qatorlar, kod qatori ("#kino #1234"), janr/sifat/til yorliq qatorlari
    ("Janri: ...") va faqat emoji'dan iborat qatorlar. Hech narsa qolmasa
    None qaytadi.
    """
    if not caption:
        return None
    text = strip_html(caption)
    kept: list[str] = []
    for raw_line in text.split("\n"):
        # HTML teg o'rniga qo'yilgan bo'shliqlar qo'shimcha ikkilanishi mumkin
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        if not line:
            continue
        if _CODE_LINE_RE.match(line):
            continue
        if _MENTION_LINE_RE.match(line):
            continue
        if _URL_RE.search(line):
            continue
        de_emoji = strip_emoji(line).strip(" :-—•")
        if _LABEL_RE.match(de_emoji):
            continue
        if is_emoji_only(line):
            continue
        kept.append(line)
    result = "\n".join(kept).strip()
    return result or None
