from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Barrier
from time import sleep

from backend.api import dependencies


def test_concurrent_first_requests_initialize_service_once(monkeypatch) -> None:
    start = Barrier(3)
    service = object()
    initialization_count = 0

    @lru_cache(maxsize=1)
    def initialize():
        nonlocal initialization_count
        initialization_count += 1
        sleep(0.1)
        return service

    monkeypatch.setattr(dependencies, "_get_rag_service_cached", initialize)

    def request_service():
        start.wait()
        return dependencies.get_rag_service()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request_service) for _ in range(2)]
        start.wait()
        results = [future.result(timeout=5) for future in futures]

    assert results == [service, service]
    assert initialization_count == 1
