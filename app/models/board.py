from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel, boards_members


class Board(BaseModel):

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by: Mapped["User"] = relationship(back_populates="owned_boards")
    
    members: Mapped[list["User"]] = relationship(
        secondary=boards_members, 
        back_populates="member_boards"
    )

    sections: Mapped[list["Section"]] = relationship(
        back_populates="board", 
        cascade="all, delete-orphan"
    )

    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan"
    )
    def __repr__(self):
        return f"Tablename = {self.__tablename__}\nBoard(name = {self.name}\ndescription={self.description})"

class Section(BaseModel):

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(200))
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False)

    board: Mapped["Board"] = relationship(back_populates="sections")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="section", cascade="all, delete-orphan")