"""HTTP Range tahlili va MTProto bo'laklash rejasi — sof mantiq, I/O yo'q.

upload.getFile cheklovlari (https://core.telegram.org/api/files):
- offset 4096 ga karrali; limit 4096 ga karrali va 1 MiB limit'ga bo'linadi;
- bitta so'rov 1 MiB chegarasini kesib o'tmaydi.
So'rov hajmi 2 ning darajasi (4 KiB..512 KiB) va boshlanish unga tekislansa,
har bir so'rov [k*rs, (k+1)*rs) bo'ladi — barcha shartlar avtomatik bajariladi.
"""

from dataclasses import dataclass

MIN_REQUEST_SIZE = 4096
MAX_REQUEST_SIZE = 512 * 1024
MIB = 1024 * 1024


@dataclass(frozen=True, slots=True)
class ByteRange:
    """Yopiq oraliq [start, end] — HTTP'dagi kabi end ham kiradi."""

    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


class RangeNotSatisfiable(ValueError):
    """Range sintaksisi xato yoki fayl hajmidan tashqarida → 416."""

    def __init__(self, size: int) -> None:
        super().__init__(f"range not satisfiable (size={size})")
        self.size = size


def _is_digits(value: str) -> bool:
    return bool(value) and value.isascii() and value.isdigit()


def _parse_spec(spec: str, size: int) -> ByteRange | None:
    """Bitta range-spec. Sintaksis xato → RangeNotSatisfiable; qanoatlantirib
    bo'lmaydigan (lekin to'g'ri yozilgan) → None."""
    first, dash, last = spec.partition("-")
    first, last = first.strip(), last.strip()
    if not dash:
        raise RangeNotSatisfiable(size)
    if not first:  # suffix: bytes=-N — oxirgi N bayt
        if not _is_digits(last):
            raise RangeNotSatisfiable(size)
        n = int(last)
        if n == 0 or size == 0:
            return None
        return ByteRange(max(size - n, 0), size - 1)
    if not _is_digits(first):
        raise RangeNotSatisfiable(size)
    start = int(first)
    if last:
        if not _is_digits(last):
            raise RangeNotSatisfiable(size)
        end = int(last)
        if end < start:
            raise RangeNotSatisfiable(size)
    else:
        end = size - 1
    if start >= size:
        return None
    return ByteRange(start, min(end, size - 1))


def parse_range_header(header: str | None, size: int) -> ByteRange | None:
    """`Range` sarlavhasini tahlil qiladi.

    None — Range yo'q (yoki noma'lum birlik, RFC 9110 bo'yicha e'tiborsiz) → 200.
    Bir nechta oraliq bo'lsa birinchi qanoatlantiriladigani qaytadi.
    """
    if header is None or not header.strip():
        return None
    unit, eq, specs = header.strip().partition("=")
    if not eq:
        raise RangeNotSatisfiable(size)
    if unit.strip().lower() != "bytes":
        return None
    chosen: ByteRange | None = None
    seen = False
    for raw in specs.split(","):
        spec = raw.strip()
        if not spec:
            continue
        seen = True
        parsed = _parse_spec(spec, size)
        if chosen is None and parsed is not None:
            chosen = parsed
    if not seen or chosen is None:
        raise RangeNotSatisfiable(size)
    return chosen


def normalize_request_size(value: int) -> int:
    """Sozlamadagi bo'lak hajmini MTProto'ga mos 2 ning darajasiga keltiradi."""
    clamped = max(MIN_REQUEST_SIZE, min(int(value), MAX_REQUEST_SIZE))
    return 1 << (clamped.bit_length() - 1)


def _valid_request_size(value: int) -> bool:
    return MIN_REQUEST_SIZE <= value <= MAX_REQUEST_SIZE and value & (value - 1) == 0


@dataclass(frozen=True, slots=True)
class ChunkPlan:
    """[start, end] baytlarini tekislangan so'rovlar bilan olish rejasi."""

    start: int
    end: int
    request_size: int

    @property
    def first_offset(self) -> int:
        return self.start - self.start % self.request_size

    @property
    def count(self) -> int:
        return self.end // self.request_size - self.start // self.request_size + 1

    @property
    def length(self) -> int:
        return self.end - self.start + 1

    def offset(self, index: int) -> int:
        return self.first_offset + index * self.request_size

    def bounds(self, index: int) -> tuple[int, int]:
        """index-bo'lakdan olinadigan [lo, hi) kesma (bo'lak boshiga nisbatan)."""
        base = self.offset(index)
        lo = max(self.start - base, 0)
        hi = min(self.end + 1 - base, self.request_size)
        return lo, hi

    def trim(self, index: int, data: bytes | memoryview) -> bytes:
        """Telegram bergan bo'lakdan faqat kerakli qismini qaytaradi."""
        if not 0 <= index < self.count:
            raise ValueError(f"bo'lak indeksi {index} rejadan tashqarida")
        lo, hi = self.bounds(index)
        if len(data) < hi:
            raise ValueError(f"bo'lak {index} qisqa: {len(data)} bayt, kamida {hi} kerak")
        return bytes(data[lo:hi])


def plan_chunks(start: int, end: int, request_size: int) -> ChunkPlan:
    if not _valid_request_size(request_size):
        raise ValueError(f"noto'g'ri request_size: {request_size}")
    if start < 0 or end < start:
        raise ValueError(f"noto'g'ri oraliq: {start}-{end}")
    return ChunkPlan(start, end, request_size)
