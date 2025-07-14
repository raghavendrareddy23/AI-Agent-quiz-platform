from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.schemas.common import PaginatedResponse
from app.schemas.quiz import QuizAttemptCreate, QuizAttemptOut, QuizCreate, QuizOut
from app.models.database import get_db
from app.services.quiz_service import QuizService
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
quiz_service = QuizService()


@router.post("/create", response_model=QuizOut)
async def create_quiz(
    quiz_data: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return quiz_service.create_quiz_from_schema(db, quiz_data, user_id=current_user.id)


@router.post("/generate", response_model=QuizOut)
async def generate_quiz(
    technology: str,
    difficulty: str,
    num_questions: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    quiz = await quiz_service.generate_quiz_with_groq(
        db, technology, difficulty, num_questions, user_id=current_user.id
    )
    if not quiz:
        raise HTTPException(
            status_code=500, detail="Failed to generate quiz from Groq API"
        )
    return quiz



@router.get("/public", response_model=PaginatedResponse[QuizOut])
def get_public_quizzes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Uncomment after testing
):
    return quiz_service.get_public_quizzes(db, page=page, limit=limit)


@router.get("/user", response_model=PaginatedResponse[QuizOut])
def get_user_quizzes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return quiz_service.get_user_quizzes(
        db, user_id=current_user.id, page=page, limit=limit
    )


@router.post("/submit", response_model=QuizAttemptOut)
def submit_quiz_attempt(
    attempt_data: QuizAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return quiz_service.create_quiz_attempt(db, attempt_data, user_id=current_user.id)


@router.get("/users/attempt", response_model=List[QuizAttemptOut])
def get_user_attempts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return quiz_service.get_user_attempts(db, user_id=current_user.id)


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz_by_id(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return quiz_service.get_quiz_by_id(db, quiz_id, current_user_id=current_user.id)
