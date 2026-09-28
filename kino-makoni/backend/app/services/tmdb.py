"""TMDB orqali poster/backdrop boyitish — ixtiyoriy (tmdb_api_key bo'lsa).

Faqat qidirish + eng mos natijani olish (kichik va oddiy). Xatolar (tarmoq,
429, formatsizlik) jimgina yutiladi — katalog sinxronizatsiyasi TMDB'siz ham
davom etishi kerak.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger("kino_makoni.tmdb")

_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"
_IMG_BASE = "https://image.tmdb.org/t/p"


async def enrich(
    client: httpx.AsyncClient, api_key: str, title: str, year: int | None
) -> dict | None:
    """Nom (va yil, bo'lsa) bo'yicha TMDB'dan eng mos natijani qaytaradi."""
    params: dict[str, str | int] = {
        "api_key": api_key,
        "query": title,
        "include_adult": "false",
    }
    if year:
        params["year"] = year
    try:
        resp = await client.get(_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("TMDB so'rovi muvaffaqiyatsiz (%s): %s", title, exc)
        return None

    results = data.get("results") or []
    if not results:
        return None
    best = results[0]
    poster_path = best.get("poster_path")
    backdrop_path = best.get("backdrop_path")
    tmdb_id = best.get("id")
    if not (poster_path or backdrop_path or tmdb_id):
        return None
    return {
        "poster_url": f"{_IMG_BASE}/w500{poster_path}" if poster_path else None,
        "backdrop_url": f"{_IMG_BASE}/w780{backdrop_path}" if backdrop_path else None,
        "tmdb_id": tmdb_id,
    }
