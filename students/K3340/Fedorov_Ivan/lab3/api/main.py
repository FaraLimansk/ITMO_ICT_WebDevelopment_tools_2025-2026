"""API gateway for direct and queued parser calls."""

from __future__ import annotations

import os
from typing import Any

import httpx
from celery.result import AsyncResult
from celery_app import celery_app
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from tasks import parse_url_task

PARSER_URL = os.getenv("PARSER_URL", "http://localhost:8001")


class ParseRequest(BaseModel):
    url: HttpUrl


app = FastAPI(title="Lab3 API Gateway", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/parse")
async def parse(request: ParseRequest) -> dict[str, Any]:
    """Call parser service over HTTP and return its response to the client."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{PARSER_URL}/parse", json={"url": str(request.url)})
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return response.json()


@app.post("/parse/async")
def parse_async(request: ParseRequest) -> dict[str, str]:
    """Queue a parser task in Celery."""

    task = parse_url_task.delay(str(request.url))
    return {"task_id": task.id, "status": "queued"}


@app.get("/tasks/{task_id}")
def task_status(task_id: str) -> dict[str, Any]:
    task = AsyncResult(task_id, app=celery_app)
    payload: dict[str, Any] = {"task_id": task_id, "status": task.status}
    if task.ready():
        payload["result"] = task.result
    return payload

