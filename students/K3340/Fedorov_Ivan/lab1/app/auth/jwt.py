"""Собственная реализация JWT (HS256) на hmac/hashlib без внешних библиотек."""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = 86_400  # токен живёт сутки


def _b64url_encode(raw: bytes) -> str:
    """base64url без выравнивающих символов '=' (требование RFC 7515)."""
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: int, username: str) -> str:
    """Собирает токен вида header.payload.signature."""
    header = {"alg": ALGORITHM, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    header_enc = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_enc = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_enc}.{payload_enc}"
    signature = hmac.new(
        SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Проверяет подпись и срок жизни. При любой ошибке возвращает None."""
    try:
        header_enc, payload_enc, signature_enc = token.split(".")
    except ValueError:
        return None

    signing_input = f"{header_enc}.{payload_enc}"
    expected = hmac.new(
        SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    try:
        given = _b64url_decode(signature_enc)
    except Exception:
        return None
    if not hmac.compare_digest(expected, given):
        return None

    try:
        payload: Dict[str, Any] = json.loads(_b64url_decode(payload_enc))
    except Exception:
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload
