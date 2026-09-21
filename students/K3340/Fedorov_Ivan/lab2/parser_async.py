"""Asyncio and aiohttp implementation of parallel page parsing."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

from parser_common import DB_PATH, PageResult, init_db, save_result


async def parse_and_save(
    session: aiohttp.ClientSession,
    url: str,
    db_path: Path = DB_PATH,
) -> PageResult:
    try:
        async with session.get(url) as response:
            html = await response.text(errors="replace")
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.get_text(strip=True) if soup.title else ""
            result = PageResult(url, title, response.status)
    except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeError, ValueError) as error:
        result = PageResult(url, "", 0, str(error))
    save_result(result, "asyncio", db_path)
    return result


async def run_async(urls: list[str], workers: int, db_path: Path = DB_PATH) -> list[PageResult]:
    init_db(db_path)
    connector = aiohttp.TCPConnector(limit=workers)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        return await asyncio.gather(*(parse_and_save(session, url, db_path) for url in urls))


def run(urls: list[str], workers: int, db_path: Path = DB_PATH) -> list[PageResult]:
    return asyncio.run(run_async(urls, workers, db_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="URLs to parse")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    for result in run(args.urls, args.workers):
        print(result)


if __name__ == "__main__":
    main()
