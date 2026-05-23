from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") 

def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm)
    
    return encoded_jwt


def verify_access_token(token: str, expected_type: str) -> str | None:
    try:
        payload = jwt.decode(
                token, 
                settings.secret_key.get_secret_value(), 
                algorithms=[settings.algorithm],
                options={"require" : ["exp", "id"]})
    except InvalidTokenError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload.get("id")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user_id = verify_access_token(token, "access")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    return user