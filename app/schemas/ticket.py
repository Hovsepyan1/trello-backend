from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TicketBase(BaseModel):
    name: str = Field(..., max_length=30, description="Name of the ticket")
    description: str = Field(..., max_length=200, description="Description of the ticket")
    due_to: datetime = Field(..., description="Deadline of ticket")

    # @field_serializer('due_to')
    # def serialize_dt(self, dt: datetime, _info):
    #     return dt.strftime('%Y-%m-%d %H:%M:%S')
    
class TicketCreate(TicketBase):
    user_id: int 

class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creator_id: int
    user_id: int
    section_id: int


class TicketUpdate(BaseModel):
    name: str | None = Field(None, max_length=30, description="Name of the ticket")
    description: str | None = Field(None, max_length=200, description="Description of the ticket")
