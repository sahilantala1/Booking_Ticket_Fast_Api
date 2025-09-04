from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        orm_mode = True

class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    date: datetime
    time: Optional[datetime] = None
    location: str
    total_seats: int

class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    date: datetime
    time: Optional[datetime]
    location: str
    total_seats: int

    class Config:
        orm_mode = True

# ✅ For multiple seat booking
class BookSeatsRequest(BaseModel):
    seats: List[int]
