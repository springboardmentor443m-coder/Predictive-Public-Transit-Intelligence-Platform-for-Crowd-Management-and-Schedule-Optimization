from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import hashlib
import hmac
import os

from app.core.config import settings


def verify_password(plain: str, hashed: str) -> bool:
    try:
        algo, salt_hex, hash_hex = hashed.split("$")
        salt = bytes.fromhex(salt_hex)
        calc = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 100_000).hex()
        return hmac.compare_digest(calc, hash_hex)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()
    return f"pbkdf2${salt.hex()}${h}"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
