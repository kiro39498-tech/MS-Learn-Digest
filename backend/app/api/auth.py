from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import GoogleAuthCode, Token

from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/google", response_model=Token)
async def google_auth(auth_data: GoogleAuthCode, db: Session = Depends(get_db)):
    """
    Exchange Google OAuth code for a JWT token.
    """
    auth_service = AuthService(db)
    jwt_token = await auth_service.exchange_google_code(auth_data.code, auth_data.redirect_uri)
    
    return {"access_token": jwt_token, "token_type": "bearer"}
