import uuid
from typing import List, Optional
from pydantic import BaseModel, EmailStr

class SettingsResponse(BaseModel):
    theme: str
    email_marketing: bool
    email_price_alerts: bool
    email_product_updates: bool

    class Config:
        from_attributes = True

class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    email_marketing: Optional[bool] = None
    email_price_alerts: Optional[bool] = None
    email_product_updates: Optional[bool] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    roles: List[str]
    settings: Optional[SettingsResponse] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str

class RoleAssignment(BaseModel):
    role: str

class StatusUpdate(BaseModel):
    is_active: bool

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None

