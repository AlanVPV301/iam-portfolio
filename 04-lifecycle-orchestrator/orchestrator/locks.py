import asyncio
from collections import defaultdict

PROCESSING_SECONDS = 5

_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def lock_for(employee_id: str) -> asyncio.Lock:
    return _locks[employee_id]
