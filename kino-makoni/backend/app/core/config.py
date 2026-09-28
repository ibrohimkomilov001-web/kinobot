"""Ilova sozlamalari — hammasi muhit o'zgaruvchilaridan (.env) o'qiladi.

Bu backend Kino Makoni iOS ilovasi uchun. Botning o'zi bilan umumiy narsa
faqat ikkita: bot bazasini FAQAT O'QISH (BOT_DATABASE_URL) va bot baza kanali
(TG_BASE_CHANNEL_ID). Botga hech narsa yozilmaydi.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ===== Umumiy =====
    app_env: str = "production"  # production | development | test
    log_level: str = "INFO"
    # Stream/thumb URL'lari shu asosda yasaladi (oxirida "/" siz)
    api_public_base_url: str = "http://localhost:8000"
    # Video trafik alohida (Cloudflare proxy'siz) domen orqali o'tishi uchun.
    # Bo'sh bo'lsa api_public_base_url ishlatiladi.
    stream_public_base_url: str = ""
    # JWT va imzolangan URL'lar uchun maxfiy kalit (kamida 32 belgi)
    secret_key: str = Field(default="dev-secret-change-me-dev-secret-change-me", min_length=32)
    cors_origins: list[str] = []

    # ===== Ilova bazasi (botnikidan ALOHIDA) =====
    database_url: str = "sqlite+aiosqlite:///./kino_makoni.db"

    # ===== Bot bazasi — FAQAT O'QISH (read-only rol) =====
    bot_database_url: str = ""  # postgresql://readonly_user:...@host/db
    catalog_sync_interval_sec: int = 300

    # ===== Telegram MTProto (alohida yordamchi bot) =====
    tg_api_id: int = 0
    tg_api_hash: str = ""
    tg_helper_bot_token: str = ""  # YANGI bot, asosiy bot tokeni EMAS
    tg_base_channel_id: int = 0  # botning maxfiy baza kanali (-100...)
    tg_session_dir: str = "./data"
    tg_chunk_size: int = 512 * 1024  # MTProto so'rov bo'lagi (bayt)

    # ===== Kontent =====
    tmdb_api_key: str = ""  # ixtiyoriy: posterlar uchun
    premium_enforced: bool = True  # premium kinolar ilovada qulflangan

    # ===== Tokenlar =====
    access_token_ttl_days: int = 30
    playback_url_ttl_sec: int = 6 * 3600

    # ===== Cloudflare R2 (keyingi bosqich: admin panel yuklashlari) =====
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = ""
    r2_public_base_url: str = ""

    @property
    def stream_base_url(self) -> str:
        return (self.stream_public_base_url or self.api_public_base_url).rstrip("/")

    @property
    def api_base_url(self) -> str:
        return self.api_public_base_url.rstrip("/")

    @property
    def telegram_enabled(self) -> bool:
        return bool(
            self.tg_api_id
            and self.tg_api_hash
            and self.tg_helper_bot_token
            and self.tg_base_channel_id
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
