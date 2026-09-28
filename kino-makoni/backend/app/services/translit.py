"""O'zbekcha transliteratsiya va nom normalizatsiyasi.

`src/utils/translit.ts` dan ANIQ Python porti (kino-makon boti). Maqsad —
foydalanuvchi nomni qaysi alifboda yozmasin (kirill/lotin), qidiruv bir xil
natija topsin. Testlar: tests/test_translit.py (translit.test.ts asosida).
"""

from __future__ import annotations

import re
import unicodedata

# Kirill → lotin (o'zbekcha + ruscha qo'shimcha belgilar). Kichik harf asos.
CYR_TO_LAT: dict[str, str] = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "'",
    "ы": "i",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    # O'zbek alifbosiga xos harflar
    "ў": "o'",
    "ғ": "g'",
    "қ": "q",
    "ҳ": "h",
    "ң": "ng",
}

# Okina/apostrof belgilarining barcha Unicode variantlari
_OKINA_RE = re.compile(r"[ʻʼ‘’`´']")
_O_FOLD_RE = re.compile(r"o[ʻʼ‘’`´']")
_G_FOLD_RE = re.compile(r"g[ʻʼ‘’`´']")


def latinize(text: str) -> str:
    """Kirill matnni lotinga o'tkazadi. Katta harflar avval kichiklashtiriladi."""
    return "".join(CYR_TO_LAT.get(ch, ch) for ch in text.lower())


def _fold_uzbek(s: str) -> str:
    """O'zbekcha digraf fold: o' → o, g' → g (va bir nechta variantlari)."""
    s = _O_FOLD_RE.sub("o", s)
    s = _G_FOLD_RE.sub("g", s)
    return _OKINA_RE.sub("", s)


def _fold_accents(s: str) -> str:
    """NFD normalizatsiya orqali aksentlarni asosiy harfdan ajratib olib tashlaydi."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s) if not (0x0300 <= ord(ch) <= 0x036F)
    )


# NFD orqali ajralmaydigan alohida belgilar
EXTRA_FOLDS: dict[str, str] = {
    "ı": "i",  # turkcha nuqtasiz i
    "ø": "o",
    "ß": "ss",
    "æ": "ae",
    "ð": "d",
    "þ": "th",
    "œ": "oe",
    "ŧ": "t",
    "ł": "l",
}
_EXTRA_RE = re.compile("[" + "".join(EXTRA_FOLDS) + "]")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_title(text: str) -> str:
    """Nomni qidiruv uchun yagona ko'rinishga keltiradi.

    kichik harf → kirill-lotin → o'/g' fold → aksent fold (NFD) → alohida
    harflar → tinish/harf bo'lmagan belgilarni bo'sh joyga aylantirish →
    ortiqcha bo'shliqlarni siqish.
    """
    s = _fold_accents(_fold_uzbek(latinize(text)))
    s = _EXTRA_RE.sub(lambda m: EXTRA_FOLDS[m.group(0)], s)
    s = _NON_ALNUM_RE.sub(" ", s)
    s = s.strip()
    return _MULTI_SPACE_RE.sub(" ", s)
