from pydantic import BaseModel, ConfigDict, Field

from .section import SectionResponse
from .user import UserPublic


class BoardBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(...,max_length=30, description="Name of the border")
    description: str = Field(..., max_length=200, description="Description of the border")

    def __repr__(self):
        return f"Board(name = {self.name}, description={self.description})"


class BoardCreate(BoardBase):
    ...

class BoardUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=30, description="Name of the border")
    description: str | None = Field(None, max_length=200, description="Description of the border")
    
class BoardResponseList(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int

class BoardResponseDetail(BoardBase):
    id: int
    owner_id: int
    members: list[UserPublic] = []
    sections: list[SectionResponse] = []

