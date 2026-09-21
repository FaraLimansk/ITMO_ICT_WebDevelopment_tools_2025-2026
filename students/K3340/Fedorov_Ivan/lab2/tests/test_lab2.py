from __future__ import annotations

import asyncio
import sqlite3

from calculation import (
    calculate_sum,
    chunks,
    sum_with_async,
    sum_with_multiprocessing,
    sum_with_threading,
)
from parser_async import run_async
from parser_common import PageResult
from parser_threading import parse_and_save


def test_chunks_cover_range_without_gaps() -> None:
    intervals = chunks(10, 3)
    assert intervals == [(1, 4), (5, 7), (8, 10)]
    assert sum(calculate_sum(*interval) for interval in intervals) == 55


def test_all_sum_implementations_match() -> None:
    expected = 500_000_500_000
    assert calculate_sum(1, 1_000_000) == expected
    assert sum_with_threading(1_000_000, 4) == expected
    assert sum_with_multiprocessing(1_000_000, 2) == expected
    assert asyncio.run(sum_with_async(1_000_000, 4)) == expected


def test_thread_parser_saves_title(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("parser_threading.fetch_sync", lambda url: PageResult(url, "Example", 200))
    db_path = tmp_path / "results.sqlite3"
    result = parse_and_save("https://example.com", db_path)
    assert result.title == "Example"
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT title, approach FROM parsed_pages").fetchone() == (
            "Example",
            "threading",
        )


def test_async_parser_saves_title(monkeypatch, tmp_path) -> None:
    class FakeResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def text(self, errors="replace"):
            return "<html><title>Async page</title></html>"

    class FakeSession:
        def get(self, url):
            return FakeResponse()

    monkeypatch.setattr("parser_async.aiohttp.ClientSession", lambda **kwargs: FakeSession())
    monkeypatch.setattr("parser_async.aiohttp.TCPConnector", lambda **kwargs: object())
    monkeypatch.setattr("parser_async.aiohttp.ClientTimeout", lambda **kwargs: object())
    db_path = tmp_path / "results.sqlite3"
    results = asyncio.run(run_async(["https://example.com"], 2, db_path))
    assert results[0].title == "Async page"
