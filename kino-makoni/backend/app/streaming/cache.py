"""Kichik LRU + TTL kesh (xotirada, bitta event loop uchun)."""

import time
from collections import OrderedDict
from collections.abc import Callable, Hashable
from typing import Generic, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    def __init__(
        self,
        maxsize: int,
        ttl_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize > 0 bo'lishi kerak")
        self._maxsize = maxsize
        self._ttl = ttl_sec
        self._clock = clock
        self._data: OrderedDict[K, tuple[float, V]] = OrderedDict()

    def get(self, key: K) -> V | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at <= self._clock():
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        self._data[key] = (self._clock() + self._ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self._maxsize:
            self._data.popitem(last=False)

    def pop(self, key: K) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def __len__(self) -> int:
        return len(self._data)
