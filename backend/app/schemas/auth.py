from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

class GoogleAuthCode(BaseModel):
    code: str
    redirect_uri: Optional[str] = None
