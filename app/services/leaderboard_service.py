from sqlalchemy.orm import Session
from app.models.user import User
from typing import List, Dict


class LeaderboardService:
    def get_leaderboard(self, db: Session, skip: int = 0, limit: int = 10):
        return (
            db.query(User).order_by(User.points.desc()).offset(skip).limit(limit).all()
        )
