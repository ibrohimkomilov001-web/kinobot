"""Barcha SQLAlchemy modellari — import qilinganda metadata'ga ro'yxatdan o'tadi."""

from app.db.base import Base
from app.models.episode import Episode
from app.models.favorite import Favorite
from app.models.progress import WatchProgress
from app.models.season import Season
from app.models.title import Title, TitleGenre
from app.models.user import User

__all__ = [
    "Base",
    "Episode",
    "Favorite",
    "Season",
    "Title",
    "TitleGenre",
    "User",
    "WatchProgress",
]
