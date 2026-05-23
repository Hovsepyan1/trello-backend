from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, delete, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..auth import get_current_user
from ..database import get_db
from ..helpers import get_pagination, get_board_with_access, get_board_with_owner_access
from ..models.base import boards_members
from ..models.board import Board, Section
from ..models.invitation import Invitation
from ..models.user import User
from ..schemas.board import (BoardCreate, BoardResponseDetail,
                             BoardResponseList, BoardUpdate)
from ..schemas.section import SectionCreate, SectionResponse

router = APIRouter()

@router.post("", response_model=BoardResponseDetail, status_code=status.HTTP_201_CREATED)
async def create_board(
    current_user: Annotated[User, Depends(get_current_user)], 
    board_in: BoardCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    data = board_in.model_dump()
    data.update({"owner_id" : current_user.id})
    new_board = Board(**data)
    db.add(new_board)
    await db.flush()
    await db.execute(insert(boards_members).values(user_id=current_user.id, board_id=new_board.id, role="Owner"))
    await db.refresh(new_board, attribute_names=["members", "sections"])
    await db.commit()
    
    return new_board    

@router.get("/all", response_model=list[BoardResponseList], status_code=status.HTTP_200_OK)
async def get_boards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Board).
        where(or_(
            Board.owner_id == current_user.id,
            Board.members.any(User.id == current_user.id)
            )
        )
        .options(selectinload(Board.members))
        )
    boards = result.scalars().all()
    return boards

@router.get("", response_model=list[BoardResponseList], status_code=status.HTTP_200_OK)
async def get_paginated_boards(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: dict = Depends(get_pagination)
):
    result = await db.execute(
        select(Board).
        where(or_(
            Board.owner_id == current_user.id,
            Board.members.any(User.id == current_user.id)
            )
        )
        .offset(pagination["offset"])
        .limit(pagination["limit"])
        .options(selectinload(Board.members))
        )

    boards = result.scalars().all()
    return boards


@router.get("/{board_id}", response_model=BoardResponseDetail, status_code=status.HTTP_200_OK)
async def get_board_by_id(
    board: Annotated[Board, Depends(get_board_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):  
    result = await db.execute(
        select(Board).
        where(Board.id == board.id).
        options(selectinload(Board.members),
                selectinload(Board.sections).selectinload(Section.tickets)))
    board = result.scalars().first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board: Annotated[Board, Depends(get_board_with_owner_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):  
    await db.delete(board)
    await db.commit()

    
@router.patch("/{board_id}", response_model=BoardResponseDetail, status_code=status.HTTP_200_OK)
async def update_board(
    board: Annotated[Board, Depends(get_board_with_owner_access)],
    board_in: BoardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    update_data = board_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(board, field, value)

    await db.commit()

    result = await db.execute(
        select(Board)
        .where(Board.id == board.id)
        .options(
            selectinload(Board.members),
            selectinload(Board.sections).selectinload(Section.tickets)
        )
    )
    
    updated_board = result.scalars().first()
    
    return updated_board

@router.post("/{board_id}/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    section_in: SectionCreate,
    board: Annotated[Board, Depends(get_board_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    new_section = Section(
        **section_in.model_dump(),
        board_id=board.id)

  
    db.add(new_section)
    await db.commit()
    await db.refresh(new_section, attribute_names=["tickets"])

    return new_section

@router.get("/{board_id}/sections", response_model=list[SectionResponse], status_code=status.HTTP_200_OK)
async def get_paginated_sections(
    board: Annotated[Board, Depends(get_board_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: dict =  Depends(get_pagination)
):
    result = await db.execute(
        select(Section)
        .join(Board, Board.id == Section.board_id)
        .where(Board.id == board.id)
        .offset(pagination["offset"])
        .limit(pagination["limit"])
        .options(selectinload(Section.tickets))
    )

    sections = result.scalars().all()
    return sections


@router.get("/{board_id}/sections/all", response_model=list[SectionResponse], status_code=status.HTTP_200_OK)
async def get_sections(
    board: Annotated[Board, Depends(get_board_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Board)
        .where(Board.id == board.id)
        .options(
            selectinload(Board.members),
            selectinload(Board.sections).selectinload(Section.tickets)
        )
    )
    board = result.scalars().first()

    return board.sections


@router.get("/{board_id}/invite", status_code=status.HTTP_200_OK)
async def invite(
    board: Annotated[Board, Depends(get_board_with_owner_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await db.execute(delete(Invitation).where(Invitation.board_id == board.id))
    
    token = uuid4().hex
    new_invitation = Invitation(
        board_id=board.id, token=token, 
        expires_at=datetime.now(UTC) + timedelta(minutes=60)
    )
    
    db.add(new_invitation)
    await db.commit()

    return {"token" : token}

@router.post("/join/{token}", response_model=dict, status_code=status.HTTP_200_OK)
async def join_to_board(
    token: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Invitation)
        .where(
            and_(
                Invitation.token == token,datetime.now(UTC) < Invitation.expires_at
            )
        )
    )
    invitation = result.scalars().first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    member_check = await db.execute(
        select(Board)
        .join(boards_members, and_(boards_members.c.board_id == invitation.board_id, boards_members.c.user_id == current_user.id))
    )
    
    if member_check.first():
        return {"message" : "User already a member"}
        
    await db.execute(
        insert(boards_members).values(
            user_id=current_user.id,
            board_id=invitation.board_id,
            role="Guest"
        )
    )
    
    await db.commit()
     
    return {"message" : "Successfully joined to board"} 
