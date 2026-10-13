from pydantic import BaseModel, EmailStr
from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role_id: int | None = None
    is_active: bool | None = None
    
class UserResponse(UserBase):
    id: int
    is_active: bool
    role: RoleResponse

    class Config:
        from_attributes = True