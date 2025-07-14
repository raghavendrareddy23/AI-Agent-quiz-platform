from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.models.database import Base

class QuizAudit(Base):
    __tablename__ = "quiz_audit"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=True)
    technology = Column(String(100))
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())
