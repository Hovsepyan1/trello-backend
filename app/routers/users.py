from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user, verify_access_token

from ..database import get_db
from ..models.token import Refresh_token
from ..models.user import User
from ..schemas.user import  UserPublic, UserUpdate

router = APIRouter()


@router.patch("", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def update_user_partially(
    current_user: Annotated[User, Depends(get_current_user)],
    user_data: UserUpdate, 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if user_data.email:
        email_query = await db.execute(select(User.email).where(User.email == user_data.email))
        if email_query.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email already registered"
            )

    updated_data = user_data.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(current_user, key, value)

    
    db.add(current_user)
    await db.commit()
    
    return current_user

@router.post("/logout",status_code=status.HTTP_204_NO_CONTENT)
async def log_out(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_id = verify_access_token(token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized or expired token"
        )
    await db.execute(
        delete(Refresh_token)
        .where(Refresh_token.token == token)
    )
    await db.commit()


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def log_out_from_all_devices(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await db.execute(
        delete(Refresh_token)
        .where(Refresh_token.user_id == current_user.id) 
    )
    await db.commit()



@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await db.delete(current_user)
    await db.commit()