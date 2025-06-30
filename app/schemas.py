# app/schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class QuizCreate(BaseModel):
    title: str
    description: str
    tags: str
    difficulty: str
    created_by: int

class QuizOut(BaseModel):
    id: int
    title: str
    description: str
    tags: str
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True
