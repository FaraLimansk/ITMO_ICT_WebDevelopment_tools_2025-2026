"""Хеширование паролей без внешних зависимостей (PBKDF2-HMAC-SHA256)."""

import hashlib
import hmac
import os

ITERATIONS = 260_000


def hash_password(plain_password: str) -> str:
    """Возвращает строку вида "<salt_hex>:<key_hex>".

    Соль генерируется случайно для каждого пароля, поэтому одинаковые
    пароли дадут разные хеши.
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode(), salt, iterations=ITERATIONS
    )
    return salt.hex() + ":" + key.hex()


def verify_password(plain_password: str, hashed: str) -> bool:
    """Сравнивает пароль с хешем за постоянное время (защита от timing-атак)."""
    try:
        salt_hex, key_hex = hashed.split(":")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    stored_key = bytes.fromhex(key_hex)
    new_key = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode(), salt, iterations=ITERATIONS
    )
    return hmac.compare_digest(stored_key, new_key)
