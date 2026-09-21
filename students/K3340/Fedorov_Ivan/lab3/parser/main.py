"""HTTP parser service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from common.parser_logic import parse_url
from common.storage import init_db, save_result
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl


class ParseRequest(BaseModel):
    url: HttpUrl


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Lab3 Parser Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/parse")
def parse(request: ParseRequest) -> dict[str, Any]:
    result = parse_url(str(request.url))
    row_id = save_result(result, "http")
    return {"id": row_id, **result.to_dict()}

