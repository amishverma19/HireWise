import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Optional
from fastapi import HTTPException, Request, status

from app.config import get_settings

logger = logging.getLogger("hirewise.auth")


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64_decode(data: str) -> bytes:
    padding = len(data) % 4
    if padding:
        data += "=" * (4 - padding)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


# --- Password Hashing with PBKDF2-HMAC-SHA256 ---

def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${hash_bytes.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash using timing-safe comparison."""
    try:
        parts = stored_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations
        ).hex()
        return secrets.compare_digest(computed, expected_hex)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# --- HS256 JWT Token Handling ---

def create_access_token(user_id: str, email: str, expires_days: int = 7) -> str:
    """Generates an HS256 JWT access token."""
    settings = get_settings()
    secret = settings.JWT_SECRET.encode("utf-8")

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + (expires_days * 86400)
    }

    encoded_header = _b64_encode(json.dumps(header).encode("utf-8"))
    encoded_payload = _b64_encode(json.dumps(payload).encode("utf-8"))
    signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")

    signature = hmac.new(secret, signature_input, hashlib.sha256).digest()
    encoded_sig = _b64_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_sig}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and cryptographically verifies an HS256 JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        encoded_header, encoded_payload, encoded_sig = parts
        settings = get_settings()
        secret = settings.JWT_SECRET.encode("utf-8")

        signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = hmac.new(secret, signature_input, hashlib.sha256).digest()

        if not secrets.compare_digest(_b64_encode(expected_sig), encoded_sig):
            return None

        payload_bytes = _b64_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp") and time.time() > payload["exp"]:
            return None

        return payload
    except Exception as e:
        logger.debug(f"JWT decode failed: {e}")
        return None


# --- FastAPI Request Dependencies ---

async def get_current_user_id_optional(request: Request) -> Optional[str]:
    """Extracts user_id from Authorization header if present, otherwise returns None."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        # Check custom header
        auth_header = request.headers.get("X-Auth-Token")
    
    if not auth_header:
        return None

    token = auth_header.replace("Bearer ", "").replace("bearer ", "").strip()
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        return payload["sub"]
    return None


async def get_current_user_id(request: Request) -> str:
    """Enforces authentication; raises 401 Unauthorized if token is missing or invalid."""
    user_id = await get_current_user_id_optional(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to access this resource.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

