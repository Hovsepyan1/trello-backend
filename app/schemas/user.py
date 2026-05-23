from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=4, max_length=20)
    last_name: str = Field(..., min_length=4, max_length=20)
    email: EmailStr = Field(..., max_length=120)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    ...

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int 
    first_name: str
    last_name: str

class UserPrivate(UserPublic):
    model_config = ConfigDict(from_attributes=True)

    email: str

class UserUpdate(UserBase):
    first_name: str | None = Field(None, min_length=5, max_length=20)
    last_name: str | None = Field(None, min_length=5, max_length=20)
    email: EmailStr | None = Field(None, max_length=120)