from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, boards_members
from .ticket import Ticket



class User(BaseModel):
    first_name: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200))

    owned_boards: Mapped[list["Board"]] = relationship(
        back_populates="created_by", 
        cascade="all, delete-orphan", 
    ) 
    member_boards: Mapped[list["Board"]] = relationship(
        secondary=boards_members, 
        back_populates="members"
    )
    created_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
        foreign_keys=[Ticket.creator_id]
    )

    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="user_assigned", 
        primaryjoin="User.id == Ticket.user_id",
        foreign_keys=[Ticket.user_id],

    )

    refresh_tokens: Mapped[list["Refresh_token"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    def __str__(self):
        return f"User({self.first_name} {self.last_name})"