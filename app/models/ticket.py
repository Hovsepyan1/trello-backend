from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Ticket(BaseModel):
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200))
    
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), nullable=False)
    
    creator: Mapped["User"] = relationship(
        back_populates="created_tickets", 
        foreign_keys=[creator_id]
    )

    user_assigned: Mapped["User"] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[user_id]
    )

    section: Mapped["Section"] = relationship(back_populates="tickets")
    
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=UTC), default=lambda: datetime.now())
    due_to: Mapped[datetime] = mapped_column(DateTime(timezone=UTC), nullable=False)
