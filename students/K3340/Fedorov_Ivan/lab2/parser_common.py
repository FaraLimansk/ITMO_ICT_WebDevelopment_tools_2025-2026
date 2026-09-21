"""Common database and parsing helpers for parser implementations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

DB_PATH = Path(__file__).with_name("parsed_pages.sqlite3")
USER_AGENT = "Fedorov-Ivan-lab2/1.0"


@dataclass(frozen=True)
class PageResult:
    url: str
    title: str
    status_code: int
    error: str | None = None


def init_db(db_path: Path = DB_PATH) -> None:
    """Create the shared results table if it does not exist."""

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS parsed_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                approach TEXT NOT NULL,
                parsed_at TEXT NOT NULL
            )
            """
        )


def save_result(result: PageResult, approach: str, db_path: Path = DB_PATH) -> None:
    """Persist one parsed page result."""

    with sqlite3.connect(db_path, timeout=30) as connection:
        connection.execute(
            "INSERT INTO parsed_pages(url, title, status_code, approach, parsed_at) VALUES (?, ?, ?, ?, ?)",
            (result.url, result.title, result.status_code, approach, datetime.now(timezone.utc).isoformat()),
        )


def parse_html(url: str, html: str, status_code: int) -> PageResult:
    title = BeautifulSoup(html, "html.parser").title
    return PageResult(url=url, title=title.get_text(strip=True) if title else "", status_code=status_code)


def fetch_sync(url: str, timeout: float = 15.0) -> PageResult:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            return parse_html(url, response.read(), response.status)
    except (OSError, TimeoutError, URLError, ValueError) as error:
        return PageResult(url=url, title="", status_code=0, error=str(error))
