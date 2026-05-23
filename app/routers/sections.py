from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from ..auth import get_current_user
from ..database import get_db
from ..helpers import get_section_with_access
from ..models import Ticket, User
from ..models.board import Board, Section
from ..schemas.section import SectionResponse, SectionUpdate
from ..schemas.ticket import TicketCreate, TicketResponse
from ..helpers import get_pagination

router = APIRouter()

@router.get("/{section_id}", response_model=SectionResponse, status_code=status.HTTP_200_OK)
async def get_section_by_id(
    section: Annotated[Section, Depends(get_section_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Section)
        .where(Section.id == section.id)
        .options(selectinload(Section.tickets))
    )
    
    section = result.scalars().first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Not found"
        )
    
    return section

@router.patch("/{section_id}", response_model=SectionResponse, status_code=status.HTTP_200_OK)
async def update_section(
    section_in: SectionUpdate,
    section: Annotated[Section, Depends(get_section_with_access)], 
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Section)
        .where(Section.id == section.id)
    )
    section = result.scalars().first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )

    update_data=section_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)

    
    db.add(section)
    await db.commit()
    await db.refresh(section, attribute_names=["tickets"])
    
    return section
    
@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_section(
    section: Annotated[Section, Depends(get_section_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await db.delete(section)
    await db.commit()
    
@router.post("/{section_id}/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    section: Annotated[Section, Depends(get_section_with_access)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Section)
        .where(Section.id == section.id)
        .options(joinedload(Section.board).selectinload(Board.members))
    )
    section = result.scalars().first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    new_ticket = Ticket(**ticket_in.model_dump(), section_id=section.id, creator_id=current_user.id)
    
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    
    return new_ticket

@router.get("/{section_id}/tickets", status_code=status.HTTP_200_OK)
async def get_paginated_tickets(
    section: Annotated[Board, Depends(get_section_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: dict =  Depends(get_pagination)
):
    result = await db.execute(
        select(Ticket)
        .join(Section, and_(Section.id == Ticket.section_id, Section.id == section.id))
        .offset(pagination["offset"])
        .limit(pagination["limit"])
    )

    sections = result.scalars().all()
    return sections

@router.get("/{section_id}/tickets/all", response_model=list[TicketResponse], status_code=status.HTTP_200_OK)
async def get_tickets(
    section: Annotated[Section, Depends(get_section_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Section)
        .where(Section.id == section.id)
        .options(joinedload(Section.board).selectinload(Board.members),
                 selectinload(Section.tickets))
    )
    section = result.scalars().first()
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Section not found"
        )
    
    return section.tickets