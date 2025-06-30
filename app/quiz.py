# app/quiz.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from . import models, schemas, database

router = APIRouter()

@router.post("/quiz")
def create_quiz(quiz: schemas.QuizCreate, db: Session = Depends(database.get_db)):
    new_quiz = models.Quiz(**quiz.dict())
    db.add(new_quiz)
    db.commit()
    return {"message": "Quiz created"}

@router.get("/quiz", response_model=list[schemas.QuizOut])
def list_quizzes(db: Session = Depends(database.get_db)):
    return db.query(models.Quiz).order_by(models.Quiz.created_at.desc()).all()
