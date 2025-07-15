from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.quiz import Quiz, Question, Option, QuizAttempt, UserAnswer
from app.schemas.quiz import (
    QuizAttemptCreate,
    QuizCreate,
    QuestionCreate,
    OptionCreate,
    AnswerSubmission,
)
from app.utils.groq_client import GroqClient
from datetime import datetime, timezone


class QuizService:
    def __init__(self):
        self.groq_client = GroqClient()

    def create_quiz_from_schema(
        self, db: Session, quiz_data: QuizCreate, user_id: int
    ) -> Quiz:
        quiz = Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            technology=quiz_data.technology,
            difficulty=quiz_data.difficulty,
            num_questions=quiz_data.num_questions,
            created_by=user_id,
            is_public=quiz_data.is_public,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        for question_data in quiz_data.questions:
            question = Question(
                quiz_id=quiz.id,
                question_text=question_data.question_text,
                explanation=question_data.explanation,
            )
            db.add(question)
            db.commit()
            db.refresh(question)

            for option_data in question_data.options:
                option = Option(
                    question_id=question.id,
                    option_text=option_data.option_text,
                    is_correct=option_data.is_correct,
                )
                db.add(option)

        db.commit()
        return quiz

    async def generate_quiz_with_groq(
        self,
        db: Session,
        technology: str,
        difficulty: str,
        num_questions: int,
        user_id: int,
    ) -> Optional[Quiz]:
        data = await self.groq_client.generate_quiz(
            technology, difficulty, num_questions
        )
        if not data:
            return None

        quiz = Quiz(
            title=data["title"],
            description=data.get("description", ""),
            technology=technology,
            difficulty=difficulty,
            num_questions=num_questions,
            created_by=user_id,
            is_public=True,
            is_ai_generated=False,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        for q in data["questions"]:
            question = Question(
                quiz_id=quiz.id,
                question_text=q["question_text"],
                explanation=q.get("explanation", ""),
            )
            db.add(question)
            db.commit()
            db.refresh(question)

            for o in q["options"]:
                option = Option(
                    question_id=question.id,
                    option_text=o["option_text"],
                    is_correct=o["is_correct"],
                )
                db.add(option)

        db.commit()
        return quiz

    def get_public_quizzes(self, db: Session, page: int = 1, limit: int = 10):
        skip = (page - 1) * limit
        total = db.query(Quiz).filter(Quiz.is_public == True).count()

        quizzes = (
            db.query(Quiz)
            .filter(Quiz.is_public == True)
            .order_by(Quiz.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {
            "page": page,
            "limit": limit,
            "total_results": total,
            "results": quizzes,
        }

    def get_user_quizzes(
        self, db: Session, user_id: int, page: int = 1, limit: int = 10
    ):
        skip = (page - 1) * limit
        total = db.query(Quiz).filter(Quiz.created_by == user_id).count()

        quizzes = (
            db.query(Quiz)
            .filter(Quiz.created_by == user_id)
            .order_by(Quiz.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return {
            "page": page,
            "limit": limit,
            "total_results": total,
            "results": quizzes,
        }

    def create_quiz_attempt(
        self, db: Session, attempt_data: QuizAttemptCreate, user_id: int
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=attempt_data.quiz_id,
            score=attempt_data.score,
            total_questions=attempt_data.total_questions,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        for answer in attempt_data.answers:
            option = (
                db.query(Option).filter(Option.id == answer.selected_option_id).first()
            )
            is_correct = option.is_correct if option else False

            user_answer = UserAnswer(
                attempt_id=attempt.id,
                question_id=answer.question_id,
                selected_option_id=answer.selected_option_id,
                is_correct=is_correct,
            )
            db.add(user_answer)

        db.commit()
        return attempt

    def get_user_attempts(self, db: Session, user_id: int) -> List[QuizAttempt]:
        return (
            db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.completed_at.desc())
            .all()
        )

    def get_quiz_by_id(self, db: Session, quiz_id: int, current_user_id: Optional[int] = None):
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Only enforce access check if the quiz is private
        if not quiz.is_public:
            if current_user_id is None or quiz.created_by != current_user_id:
                raise HTTPException(
                    status_code=403, detail="You do not have access to this quiz"
                )

        return quiz

