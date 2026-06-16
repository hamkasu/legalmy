from pydantic import BaseModel, EmailStr
from datetime import datetime

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organisation: str
    role: str = "user"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    organisation: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
