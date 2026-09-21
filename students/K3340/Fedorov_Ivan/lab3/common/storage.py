"""PostgreSQL storage for parsed pages."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg2
from psycopg2.extensions import connection as PgConnection

from common.parser_logic import ParseResult

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/finance_db")


def connect() -> PgConnection:
    return psycopg2.connect(DB_URL)


def init_db() -> None:
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS parsed_pages (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    parsed_at TIMESTAMPTZ NOT NULL,
                    error TEXT
                )
                """
        )


def save_result(result: ParseResult, source: str) -> int:
    init_db()
    with connect() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO parsed_pages(url, title, status_code, source, parsed_at, error)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                result.url,
                result.title,
                result.status_code,
                source,
                datetime.now(timezone.utc),
                result.error,
            ),
        )
        inserted_id = cursor.fetchone()[0]
    return int(inserted_id)
