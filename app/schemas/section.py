from pydantic import BaseModel, ConfigDict, Field

from .ticket import TicketResponse


class SectionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=30, description="Name of the border")
    description: str = Field(..., max_length=200, description="Description of the border")

class SectionResponse(SectionBase):

    id: int
    board_id: int
    tickets: list["TicketResponse"] = []

class SectionCreate(SectionBase):
    ...

class SectionUpdate(BaseModel):
    name: str | None = Field(None, max_length=30, description="Name of the border")
    description: str | None = Field(None, description="Description of the border")

