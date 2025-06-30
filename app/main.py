# app/main.py
from fastapi import FastAPI
from .database import Base, engine
from . import auth, quiz

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Quiz Platform - Stage 1")

app.include_router(auth.router, prefix="/auth")
app.include_router(quiz.router, prefix="/api")
