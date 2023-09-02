from pydantic import BaseModel, conint, EmailStr
from typing import Union, Optional


class Feedback(BaseModel):
    name: str
    message: str


class User(BaseModel):
    username: str
    password: str
    role: Optional[str] = None


class TodoCreate(BaseModel):
    title: str
    description: str
    completed: bool = False


class TodoReturn(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    completed: bool = False


class UserCreate(BaseModel):
    username: str
    email: str


class UserReturn(BaseModel):
    username: str
    email: str
    id: Optional[int] = None
