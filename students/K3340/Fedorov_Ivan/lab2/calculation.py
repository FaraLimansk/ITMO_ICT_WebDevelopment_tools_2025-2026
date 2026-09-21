"""Compare threading, multiprocessing and asyncio for a CPU-bound sum."""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import asdict

from benchmarks import BenchmarkResult, benchmark

DEFAULT_LIMIT = 10_000_000_000_000


def calculate_sum(start: int, end: int) -> int:
    """Return the inclusive sum of an interval."""

    count = end - start + 1
    return (start + end) * count // 2


def chunks(limit: int, workers: int) -> list[tuple[int, int]]:
    """Split 1..limit into balanced inclusive intervals."""

    if limit < 1 or workers < 1:
        raise ValueError("limit and workers must be positive")
    workers = min(workers, limit)
    base, remainder = divmod(limit, workers)
    result = []
    start = 1
    for index in range(workers):
        size = base + (index < remainder)
        end = start + size - 1
        result.append((start, end))
        start = end + 1
    return result


def sum_with_threading(limit: int, workers: int) -> int:
    """Calculate interval sums in worker threads."""

    intervals = chunks(limit, workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return sum(executor.map(lambda pair: calculate_sum(*pair), intervals))


def sum_with_multiprocessing(limit: int, workers: int) -> int:
    """Calculate interval sums in worker processes."""

    intervals = chunks(limit, workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return sum(executor.map(_calculate_interval, intervals))


def _calculate_interval(pair: tuple[int, int]) -> int:
    return calculate_sum(*pair)


async def _async_interval(start: int, end: int) -> int:
    """Yield control between CPU chunks to demonstrate asyncio scheduling."""

    await asyncio.sleep(0)
    return calculate_sum(start, end)


async def sum_with_async(limit: int, workers: int) -> int:
    """Schedule interval calculations as asyncio tasks."""

    return sum(await asyncio.gather(*(_async_interval(*pair) for pair in chunks(limit, workers))))


def run_benchmarks(limit: int, workers: int) -> list[BenchmarkResult]:
    expected = calculate_sum(1, limit)
    results = [
        benchmark("threading", workers, lambda: sum_with_threading(limit, workers), int),
        benchmark("multiprocessing", workers, lambda: sum_with_multiprocessing(limit, workers), int),
        benchmark("asyncio", workers, lambda: asyncio.run(sum_with_async(limit, workers)), int),
    ]
    if any(item.result != expected for item in results):
        raise RuntimeError("parallel implementations returned different results")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--workers", type=int, default=multiprocessing.cpu_count())
    args = parser.parse_args()
    print(json.dumps([asdict(item) for item in run_benchmarks(args.limit, args.workers)], indent=2))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
