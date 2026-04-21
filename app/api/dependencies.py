"""
Dépendances FastAPI.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.api.rate_limiter import RateLimiter

security = HTTPBearer()
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Valide le token JWT et retourne l'utilisateur."""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"authenticated": True, "payload": payload}


async def check_rate_limit(request: Request):
    """Vérifie la limite de taux pour une requête."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de requêtes. Veuillez réessayer plus tard.",
        )
    
    return client_ip