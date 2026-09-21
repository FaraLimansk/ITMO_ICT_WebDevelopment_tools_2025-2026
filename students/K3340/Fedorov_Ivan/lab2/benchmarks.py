"""Shared benchmark helpers for the three execution models."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of one benchmark run."""

    name: str
    workers: int
    elapsed_seconds: float
    result: int


def benchmark(
    name: str,
    workers: int,
    operation: Callable[[], T],
    result_to_int: Callable[[T], int],
) -> BenchmarkResult:
    """Measure an operation with a monotonic clock."""

    started = time.perf_counter()
    result = operation()
    elapsed = time.perf_counter() - started
    return BenchmarkResult(name, workers, elapsed, result_to_int(result))
