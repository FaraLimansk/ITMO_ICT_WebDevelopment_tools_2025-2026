"""HTML loading and title extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Fedorov-Ivan-lab3/1.0"


@dataclass(frozen=True)
class ParseResult:
    url: str
    title: str
    status_code: int
    error: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        return asdict(self)


def parse_url(url: str, timeout: float = 15.0) -> ParseResult:
    """Download a page and extract its title."""

    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return ParseResult(url=url, title="", status_code=0, error=str(error))

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    return ParseResult(url=url, title=title, status_code=response.status_code)

