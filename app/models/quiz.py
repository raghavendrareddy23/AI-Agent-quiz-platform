from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    technology = Column(String(100))
    difficulty = Column(String(50))
    num_questions = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    is_public = Column(Boolean, default=True)
    is_ai_generated = Column(Boolean, default=False)

    questions = relationship(
        "Question", back_populates="quiz", cascade="all, delete-orphan"
    )
    attempts = relationship("QuizAttempt", back_populates="quiz")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"))
    question_text = Column(Text, nullable=False)
    explanation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    quiz = relationship("Quiz", back_populates="questions")
    options = relationship(
        "Option", back_populates="question", cascade="all, delete-orphan"
    )


class Option(Base):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="options")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    quiz_id = Column(
        Integer, ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True
    )
    score = Column(Integer)
    total_questions = Column(Integer)
    completed_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship(
        "UserAnswer", back_populates="attempt", cascade="all, delete-orphan"
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    selected_option_id = Column(Integer, ForeignKey("options.id"))
    is_correct = Column(Boolean)
    created_at = Column(DateTime, server_default=func.now())

    attempt = relationship("QuizAttempt", back_populates="answers")
    question = relationship("Question")
    selected_option = relationship("Option")


class QuizTrend(Base):
    __tablename__ = "quiz_trends"

    id = Column(Integer, primary_key=True, index=True)
    technology = Column(String(100), unique=True, index=True)
    popularity_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    technology = Column(String(100))
    interaction_score = Column(Float, default=0.0)
    last_interaction = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="activities")
