from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints
from app.schemas.role import RoleResponse


Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9_.-]+$"
    )
]

FullName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=100)
]

# bcrypt only uses the first 72 bytes of a password.
Password = Annotated[
    str,
    StringConstraints(min_length=8, max_length=72)
]


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    username: Username
    full_name: FullName | None = None
    password: Password


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: FullName | None = None
    role_id: int | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    role: RoleResponse

    model_config = ConfigDict(from_attributes=True)
