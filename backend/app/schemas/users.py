from pydantic import BaseModel, ConfigDict, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserPublic(UserBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str | None = None
