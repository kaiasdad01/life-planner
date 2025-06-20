from typing import Optional
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    partner_id: Optional[UUID4] = None
    partnership_status: Optional[str] = None


class UserInDB(UserBase):
    id: UUID4
    is_active: bool
    is_verified: bool
    partner_id: Optional[UUID4] = None
    partnership_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None 