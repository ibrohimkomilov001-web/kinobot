"""Stream moduli ichki xatolari. Router ularni HTTP javobga aylantiradi."""


class StreamError(Exception):
    """Barcha stream xatolarining asosi."""


class BackendUnavailable(StreamError):
    """Telegram ulanmagan yoki javob bermayapti (503 unavailable)."""


class MediaNotFound(StreamError):
    """Xabar yo'q yoki unda video/rasm yo'q (404)."""


class FileRefExpired(StreamError):
    """file_reference eskirgan — xabarni qayta olib, davom ettirish kerak."""


class FloodWait(StreamError):
    """Telegram FLOOD_WAIT: `seconds` soniya kutish kerak."""

    def __init__(self, seconds: int) -> None:
        self.seconds = max(int(seconds or 0), 0)
        super().__init__(f"flood wait {self.seconds}s")


class Busy(StreamError):
    """Parallel Telegram so'rovlari limiti to'lgan va navbat kutish muddati o'tdi."""


class StreamBroken(StreamError):
    """Telegram kutilmagan ma'lumot qaytardi (qisqa bo'lak, video almashgan...)."""
