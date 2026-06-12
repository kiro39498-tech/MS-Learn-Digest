"""
Auth Service
Handles Google OAuth token exchange and user provisioning.
"""

import httpx
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        
    async def exchange_google_code(self, code: str, redirect_uri: str) -> str:
        """
        Exchanges a Google OAuth authorization code for an access token,
        fetches user profile, creates/updates user in DB, and returns a JWT.
        """
        # 1. Exchange code for Google access token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=data)
            if token_response.status_code != 200:
                logger.error(f"Google token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google OAuth code"
                )
                
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # 2. Fetch user profile from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            userinfo_response = await client.get(userinfo_url, headers=headers)
            
            if userinfo_response.status_code != 200:
                logger.error(f"Google userinfo failed: {userinfo_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to fetch Google profile"
                )
                
            user_info = userinfo_response.json()
            
        # 3. Find or Create User in DB
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")
        
        user = self.db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            # Check by email just in case
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                # Update google ID
                user.google_id = google_id
            else:
                # Create new user
                user = User(
                    google_id=google_id,
                    email=email,
                    name=name,
                    avatar_url=picture
                )
                self.db.add(user)
                
        # Always update picture and name to keep it fresh
        user.name = name
        user.avatar_url = picture
        
        self.db.commit()
        self.db.refresh(user)
        
        # 4. Generate our own JWT
        jwt_token = create_access_token(data={"sub": str(user.id)})
        return jwt_token
