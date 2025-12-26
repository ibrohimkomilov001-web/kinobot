from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from handlers.movie_handlers import router as movie_router

__all__ = ['user_router', 'admin_router', 'movie_router']
