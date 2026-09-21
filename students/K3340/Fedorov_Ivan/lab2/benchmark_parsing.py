"""Measure parsing time for threading, multiprocessing and asyncio."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Callable

from parser_async import run as run_async
from parser_multiprocessing import run as run_multiprocessing
from parser_threading import run as run_threading


def measure(
    name: str,
    operation: Callable,
    urls: list[str],
    workers: int,
    db_path: Path,
) -> None:
    started = time.perf_counter()
    results = operation(urls, workers, db_path)
    elapsed = time.perf_counter() - started
    successful = sum(result.status_code == 200 for result in results)
    print(f"{name:<17} {elapsed:>10.4f} s   pages: {successful}/{len(results)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--db", type=Path, default=Path("parsed_pages.sqlite3"))
    args = parser.parse_args()

    print(f"URLs: {len(args.urls)} | workers: {args.workers}")
    print("-" * 52)
    measure("threading", run_threading, args.urls, args.workers, args.db)
    measure("multiprocessing", run_multiprocessing, args.urls, args.workers, args.db)
    measure("asyncio", run_async, args.urls, args.workers, args.db)


if __name__ == "__main__":
    main()
