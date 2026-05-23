from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class InvitationToken(BaseModel):
    token: str
    expires_at: int