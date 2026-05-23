from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import get_current_user
from .database import get_db
from .models import Board, Section, Ticket, User


def get_pagination(
    offset: int = 0,
    limit: int = 10,
):
    if offset < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offset cannot be negative") 
    
    limit = min(limit, 50)
    if limit < 0:
        limit = 10
        
    return {"offset": offset, "limit": limit}

async def get_board_with_access(
    board_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Board:
    result = await db.execute(
        select(Board)
        .where(Board.id == board_id)
    )
    board = result.scalars().first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    result = await db.execute(
        select(Board)
        .where(
            and_(
                Board.id == board_id,
                or_(
                    Board.owner_id == current_user.id,
                    Board.members.any(User.id == current_user.id)
                )
            )
        )
    )
    board = result.scalars().first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this board"
        )

    return board

async def get_board_with_owner_access(
    board_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Board:

    result = await db.execute(
        select(Board)
        .where(Board.id == board_id)
    )
    board = result.scalars().first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found"
        )
    
    result = await db.execute(
        select(Board)
        .where(
            and_(
                Board.id == board_id,
                    Board.owner_id == current_user.id,
            )
        )
    )
    board = result.scalars().first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this board"
        )

    return board


async def get_section_with_access(
    section_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Section)
        .where(Section.id == section_id)
    )

    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    result = await db.execute(
        select(Section)
        .join(Board, Section.board_id == Board.id)
        .where(
            and_(
                Section.id == section_id,
                or_(Board.owner_id == current_user.id,
                    Board.members.any(User.id == current_user.id)
                )
            )

        )
    )
    section = result.scalars().first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this section"
        )
    
    return section

async def get_ticket_with_access(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Ticket:
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id)
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    result = await db.execute(
        select(Ticket)
        .join(Section, Section.id == Ticket.section_id)
        .join(Board, Board.id == Section.board_id)
        .where(
            Ticket.id == ticket_id,
            or_(
                    Board.owner_id == current_user.id,
                    Ticket.creator_id == current_user.id,
                )
            )
        )
    
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this ticket"
        )
    
    return ticket