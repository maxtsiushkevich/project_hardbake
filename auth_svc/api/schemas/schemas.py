from pydantic import BaseModel

from api.core.roles import Role


class UserBase(BaseModel):
    username: str
    role: Role

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True