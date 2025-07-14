from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OptionCreate(BaseModel):
    option_text: str
    is_correct: bool


class OptionOut(BaseModel):
    id: int
    question_id: int
    option_text: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    question_text: str
    explanation: Optional[str] = None
    options: List[OptionCreate]


class QuestionOut(BaseModel):
    id: int
    quiz_id: int
    question_text: str
    explanation: Optional[str]
    options: List[OptionOut]

    class Config:
        from_attributes = True


class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    technology: str
    difficulty: str
    num_questions: int
    is_public: bool = True
    questions: List[QuestionCreate]


class QuizOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    technology: str
    difficulty: str
    num_questions: int
    created_by: int
    created_at: datetime
    is_public: bool
    is_ai_generated: Optional[bool] = False
    questions: List[QuestionOut]

    class Config:
        from_attributes = True


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option_id: int


class QuizAttemptCreate(BaseModel):
    quiz_id: int
    score: int
    total_questions: int
    answers: List[AnswerSubmission]


class QuizAttemptOut(BaseModel):
    id: int
    user_id: int
    quiz_id: int
    score: int
    total_questions: int
    completed_at: datetime

    class Config:
        from_attributes = True


class QuizTrendOut(BaseModel):
    id: int
    technology: str
    popularity_score: float
    last_updated: datetime

    class Config:
        from_attributes = True


class UserActivityOut(BaseModel):
    id: int
    technology: str
    interaction_score: float
    last_interaction: datetime

    class Config:
        from_attributes = True
