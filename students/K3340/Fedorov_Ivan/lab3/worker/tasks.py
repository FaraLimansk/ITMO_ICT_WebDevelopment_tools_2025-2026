"""Background parser tasks."""

from __future__ import annotations

from typing import Any

from celery_app import celery_app
from common.parser_logic import parse_url
from common.storage import save_result


@celery_app.task(name="parse_url_task")
def parse_url_task(url: str) -> dict[str, Any]:
    result = parse_url(url)
    row_id = save_result(result, "celery")
    return {"id": row_id, **result.to_dict()}

