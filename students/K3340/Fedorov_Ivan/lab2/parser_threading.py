"""Threading implementation of parallel page parsing."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from parser_common import DB_PATH, PageResult, fetch_sync, init_db, save_result


def parse_and_save(url: str, db_path: Path = DB_PATH) -> PageResult:
    result = fetch_sync(url)
    save_result(result, "threading", db_path)
    return result


def run(urls: list[str], workers: int, db_path: Path = DB_PATH) -> list[PageResult]:
    init_db(db_path)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(lambda url: parse_and_save(url, db_path), urls))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="URLs to parse")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    for result in run(args.urls, args.workers):
        print(result)


if __name__ == "__main__":
    main()

