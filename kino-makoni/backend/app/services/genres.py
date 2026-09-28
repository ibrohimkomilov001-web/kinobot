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


# Ruscha/inglizcha/katta-kichik harfli variantlar → yagona o'zbekcha nom.
# Kalitlar normalize_title() orqali solishtiriladi ("драма" → "drama").
_CANONICAL_SOURCE: dict[str, list[str]] = {
    "Drama": ["drama", "драма"],
    "Komediya": ["komediya", "комедия", "comedy"],
    "Jangari": ["jangari", "боевик", "action", "экшн"],
    "Triller": ["triller", "триллер", "thriller"],
    "Melodrama": ["melodrama", "мелодрама"],
    "Romantika": ["romantika", "романтика", "романтический", "romance"],
    "Sarguzasht": ["sarguzasht", "приключения", "приключение", "adventure"],
    "Oilaviy": ["oilaviy", "семейный", "семейное", "family"],
    "Fantastika": ["fantastika", "фантастика", "sci-fi", "science fiction"],
    "Fentezi": ["fentezi", "фэнтези", "fantasy"],
    "Qo'rqinchli": ["qo'rqinchli", "qorqinchli", "ужасы", "ужас", "horror"],
    "Detektiv": ["detektiv", "детектив", "mystery"],
    "Kriminal": ["kriminal", "криминал", "crime"],
    "Tarixiy": ["tarixiy", "исторический", "история", "history"],
    "Harbiy": ["harbiy", "военный", "война", "war"],
    "Multfilm": ["multfilm", "мультфильм", "animation", "cartoon"],
    "Biografiya": ["biografiya", "биография", "biography"],
    "Hujjatli": ["hujjatli", "документальный", "documentary"],
    "Anime": ["anime", "аниме"],
    "Sport": ["sport", "спорт"],
    "Myuzikl": ["myuzikl", "мюзикл", "musical"],
    "Vestern": ["vestern", "вестерн", "western"],
}
_CANONICAL: dict[str, str] = {
    normalize_title(alias): canonical
    for canonical, aliases in _CANONICAL_SOURCE.items()
    for alias in aliases
}


def canonical_genre(name: str) -> str:
    """Janr nomini yagona ko'rinishga keltiradi (lug'atda bo'lmasa — bosh harf katta)."""
    known = _CANONICAL.get(normalize_title(name))
    if known:
        return known
    return name[:1].upper() + name[1:]


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
        name = canonical_genre(name)
        slug = genre_slug(name)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append((name, slug))
    return out
