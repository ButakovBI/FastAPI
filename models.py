from pydantic import BaseModel, conint, EmailStr
from typing import Union


class Feedback(BaseModel):
    name: str
    message: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Union[conint(gt=0), None] = None
    is_subscribed: Union[bool, None] = None


class User(BaseModel):
    name: str
    password: str
