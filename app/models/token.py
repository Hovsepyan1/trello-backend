from datetime import UTC, datetime

from sqlalchemy import BOOLEAN, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .user import User


class Refresh_token(BaseModel):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(256), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=UTC))

    user: Mapped[User] = relationship(back_populates="refresh_tokens")