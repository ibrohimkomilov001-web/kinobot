"""Bot'ning erkin matn janr ustunini (masalan "Jangari, Drama") ayirib olish.

Bo'linish belgilari: `,` `/` `|` va o'zbekcha bog'lovchi "va". Har bir bo'lak
emoji/`#`'dan tozalanadi; slug `normalize_title` orqali yasaladi (bo'shliqlar
`-` bilan) — /v1/genres va /v1/titles?genre= filtri shu slug'ga tayanadi.
"""

from __future__ import annotations

import re

from app.services.text_clean import strip_emoji
from app.services.translit import normalize_title

_SPLIT_RE = re.compile(r"[,/|]|\bva\b", re.IGNORECASE | re.UNICODE)
_STRIP_CHARS = " \t.,-–—•#"


def genre_slug(name: str) -> str:
    return normalize_title(name).replace(" ", "-")


def parse_genres(raw: str | None) -> list[tuple[str, str]]:
    """`raw`dan (ko'rsatiladigan_nom, slug) juftliklarini qaytaradi (takrorsiz)."""
    if not raw:
        return []
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for part in _SPLIT_RE.split(raw):
        name = strip_emoji(part).strip(_STRIP_CHARS)
        if not name:
            continue
        slug = genre_slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append((name, slug))
    return out
