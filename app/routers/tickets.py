from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..helpers import get_ticket_with_access
from ..models import Ticket
from ..schemas import TicketResponse, TicketUpdate

router = APIRouter()

@router.get("/{ticket_id}", response_model=TicketResponse, status_code=status.HTTP_200_OK)
async def get_ticket_by_id(
    ticket: Annotated[Ticket, Depends(get_ticket_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Ticket:
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(joinedload(Ticket.section)
        )
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse, status_code=status.HTTP_200_OK)
async def update_ticket(
    ticket_in: TicketUpdate,
    ticket: Annotated[Ticket, Depends(get_ticket_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Ticket:
    
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(joinedload(Ticket.section))
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in ticket_data.items():
        setattr(ticket, field, value)

    db.add(ticket)
    await db.commit()
   
    return ticket
    

@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket: Annotated[Ticket, Depends(get_ticket_with_access)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    await db.delete(ticket)
    await db.commit()   