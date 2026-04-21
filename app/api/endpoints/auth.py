"""
Endpoint d'authentification.
"""
from fastapi import APIRouter, HTTPException, status
from datetime import timedelta
import structlog

from pydantic import BaseModel

from app.core.security import verify_pin, create_access_token
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])


class PinRequest(BaseModel):
    pin: str


class PinResponse(BaseModel):
    token: str
    expires_in: int
    token_type: str = "Bearer"


@router.post("/verify-pin", response_model=PinResponse)
async def verify_pin_endpoint(request: PinRequest):
    """
    Vérifie le PIN et retourne un token JWT.
    
    PIN requis : 08042026
    """
    if not verify_pin(request.pin):
        logger.warning("auth_failed", reason="invalid_pin")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Code PIN incorrect",
        )
    
    token = create_access_token(
        data={"authenticated": True, "user": "admin"},
        expires_delta=timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    )
    
    logger.info("auth_success")
    
    return PinResponse(
        token=token,
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600,
    )


@router.post("/refresh")
async def refresh_token(user=Depends(get_current_user)):
    """Rafraîchit le token JWT."""
    token = create_access_token(
        data={"authenticated": True, "user": "admin"},
        expires_delta=timedelta(hours=settings.JWT_EXPIRATION_HOURS),
    )
    return {"token": token, "expires_in": settings.JWT_EXPIRATION_HOURS * 3600}