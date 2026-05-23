from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import (DeclarativeBase, Mapped, declared_attr,
                            mapped_column, relationship)


class BaseModel(DeclarativeBase):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__qualname__.lower() + "s"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, nullable=False)

boards_members=Table(
    "boards_members", 
    BaseModel.metadata, 
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("board_id", ForeignKey("boards.id"), primary_key=True),
    Column("role", String(6), nullable=False)
)
