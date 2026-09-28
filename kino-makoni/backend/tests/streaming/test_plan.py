"""Tekislash/kesish rejasi: bo'laklar yig'indisi aynan so'ralgan baytlar bo'lishi kerak."""

import random

import pytest

from app.streaming.ranges import ByteRange, plan_chunks
from app.streaming.streamer import Streamer
from tests.streaming.fakes import ConstraintViolation, FakeBackend, check_get_file, pattern_bytes

MIB = 1024 * 1024
REQUEST_SIZES = [4096, 8192, 64 * 1024, 128 * 1024, 256 * 1024, 512 * 1024]


def fetch_via_plan(data: bytes | memoryview, start: int, end: int, request_size: int) -> bytes:
    """Rejani qat'iy soxta getFile bilan bajaradi."""
    plan = plan_chunks(start, end, request_size)
    out = bytearray()
    for i in range(plan.count):
        off = plan.offset(i)
        check_get_file(off, request_size, len(data))
        out += plan.trim(i, data[off : off + request_size])
    return bytes(out)


def random_case(rng: random.Random) -> tuple[int, int, int, int]:
    rs = rng.choice(REQUEST_SIZES)
    size = rng.choice(
        [
            rng.randint(1, 10),
            rng.randint(1, 3 * rs),
            rng.randint(1, min(5 * MIB, 64 * rs)),  # 1 MiB chegaralari ham kiradi
            rs * rng.randint(1, 8),  # aniq karrali hajm (EOF chegarasi)
            rs * rng.randint(1, 8) + rng.choice([-1, 1]),
        ]
    )
    size = max(size, 1)
    kind = rng.random()
    if kind < 0.15:
        start, end = 0, size - 1
    elif kind < 0.3:  # bitta bayt
        start = rng.randrange(size)
        end = start
    elif kind < 0.45:  # bo'lak chegaralari atrofida
        k = rng.randint(0, max(size // rs, 0))
        start = min(max(k * rs + rng.choice([-1, 0, 1]), 0), size - 1)
        end = min(start + rng.choice([0, rs - 1, rs, rs + 1, 2 * rs]), size - 1)
    else:
        start = rng.randrange(size)
        end = rng.randrange(start, size)
    return size, start, end, rs


def test_plan_random_exact_bytes() -> None:
    rng = random.Random(20260928)
    master = memoryview(pattern_bytes(6 * MIB, seed=11))  # nusxasiz kesiladi
    for _ in range(3000):
        size, start, end, rs = random_case(rng)
        data = master[:size]
        got = fetch_via_plan(data, start, end, rs)
        assert got == data[start : end + 1], (size, start, end, rs)


def test_plan_counts_and_alignment() -> None:
    plan = plan_chunks(10, 10, 4096)
    assert (plan.first_offset, plan.count, plan.bounds(0)) == (0, 1, (10, 11))
    plan = plan_chunks(4095, 4096, 4096)
    assert plan.count == 2
    assert plan.bounds(0) == (4095, 4096)
    assert plan.bounds(1) == (0, 1)
    plan = plan_chunks(MIB - 1, MIB, 512 * 1024)
    assert [plan.offset(i) for i in range(plan.count)] == [512 * 1024, MIB]


def test_plan_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        plan_chunks(0, 10, 3000)  # 4096 ga karrali emas
    with pytest.raises(ValueError):
        plan_chunks(0, 10, 12288)  # 1 MiB'ni bo'lmaydi
    with pytest.raises(ValueError):
        plan_chunks(0, 10, 1024 * 1024)  # 512 KiB'dan katta
    with pytest.raises(ValueError):
        plan_chunks(10, 5, 4096)
    with pytest.raises(ValueError):
        plan_chunks(0, 10, 4096).trim(0, b"short")  # kerakli baytlar yetmaydi


def test_fake_enforces_constraints() -> None:
    with pytest.raises(ConstraintViolation):
        check_get_file(100, 4096, 10**6)
    with pytest.raises(ConstraintViolation):
        check_get_file(0, 12288, 10**6)
    with pytest.raises(ConstraintViolation):
        check_get_file(MIB - 4096, 8192, 10**7)  # 1 MiB chegarasini kesadi
    with pytest.raises(ConstraintViolation):
        check_get_file(8192, 4096, 8192)  # fayldan tashqarida


async def test_streamer_random_ranges_exact_bytes() -> None:
    """To'liq yo'l: Streamer → soxta backend (cheklovlar tekshiriladi) → trim."""
    rng = random.Random(7)
    for _ in range(250):
        size, start, end, rs = random_case(rng)
        data = pattern_bytes(size, seed=rng.randint(0, 250))
        backend = FakeBackend()
        backend.add(1, data)
        streamer = Streamer(backend, channel_id=-1001, chunk_size=rs)
        media = await streamer.get_media(1)
        stream = streamer.open_stream(1, media, ByteRange(start, end))
        await stream.prefetch()
        body = b"".join([chunk async for chunk in stream])
        await stream.aclose()
        assert body == data[start : end + 1], (size, start, end, rs)
        expected_requests = plan_chunks(start, end, rs).count
        assert len(backend.requests) == expected_requests
        assert backend.open_iterators == 0
