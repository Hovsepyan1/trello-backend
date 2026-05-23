from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (create_access_token, hash_password,
                    verify_access_token, verify_password)
from ..config import settings
from ..database import get_db
from ..models.token import Refresh_token
from ..models.user import User
from ..schemas.token import LoginResponse
from ..schemas.user import UserCreate, UserPublic

router = APIRouter()

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(User.email).where(
            func.lower(User.email) == user_in.email.lower()
        )
    )
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user with this username already exists",
        )

    new_user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(User)
        .where(form_data.username.lower() == func.lower(User.email)
        )
    )
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Incorrect email or password"
        )
    access_token_expire = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        {"id": user.id, "type": "access"},
        expires_delta=access_token_expire
        )
    refresh_token_expire = timedelta(minutes=settings.refresh_token_expire_minutes)
    refresh_token = create_access_token(
        {"id": user.id, "type": "refresh"},
        expires_delta=refresh_token_expire
    )
    db_token = Refresh_token(
        token=refresh_token,
        user_id=user.id,
        expires_at=datetime.now() + timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    db.add(db_token)
    await db.commit()

    return LoginResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_id = verify_access_token(token, "refresh")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    result = await db.execute(
        select(Refresh_token)
        .where(
            and_(
                Refresh_token.token==token,
                Refresh_token.user_id == user_id
            )
        )
    )
    existing_token = result.scalars().first()
    if not existing_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="refresh token not found"
        )
    
    await db.execute(
        delete(Refresh_token)
        .where(
            and_(
                Refresh_token.token==token,
                Refresh_token.user_id == user_id
            )
        )
    )
    await db.commit()

    access_token = create_access_token(
        {"id": user_id, "type": "access"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_access_token(
        {"id": user_id, "type": "refresh"},
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes)
    )
    
    db_token = Refresh_token(
        token=refresh_token,
        user_id=int(user_id),
        expires_at=datetime.now() + timedelta(minutes=settings.refresh_token_expire_minutes),
    )

    db.add(db_token)
    await db.commit()

    return {"access_token" : access_token, "refresh_token" : refresh_token}
