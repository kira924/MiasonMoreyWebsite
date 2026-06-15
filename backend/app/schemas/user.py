from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for incoming data when a user registers
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

# Schema for outgoing data (hiding the password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None