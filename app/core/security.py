"""
Sécurité : PIN et JWT.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import json
import base64

from app.core.config import settings

try:
    from jose import jwt, JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False


def verify_pin(plain_pin: str) -> bool:
    """Vérifie le code PIN."""
    return plain_pin == settings.PIN_CODE


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT."""
    if JOSE_AVAILABLE:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS))
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    else:
        payload = {
            "data": data,
            "exp": (datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)).isoformat(),
            "iat": datetime.utcnow().isoformat(),
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Décode un token JWT."""
    if JOSE_AVAILABLE:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except Exception:
            return None
    else:
        try:
            payload = json.loads(base64.b64decode(token.encode()).decode())
            exp = datetime.fromisoformat(payload["exp"])
            if datetime.utcnow() > exp:
                return None
            return payload["data"]
        except Exception:
            return None


def generate_secure_key(length: int = 32) -> str:
    """Génère une clé sécurisée."""
    import secrets
    return secrets.token_hex(length)