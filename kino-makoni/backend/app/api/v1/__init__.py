"""`/v1` router agregatori."""

from fastapi import APIRouter

from app.api.v1 import auth, genres, home, me, playback, search, titles

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(home.router)
router.include_router(titles.router)
router.include_router(genres.router)
router.include_router(search.router)
router.include_router(playback.router)
router.include_router(me.router)

__all__ = ["router"]
