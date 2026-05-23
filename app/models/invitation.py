from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Invitation(BaseModel):
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"))
    token: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=UTC),default=lambda:datetime.now(UTC))

    board: Mapped["Board"] = relationship(back_populates="invitations")