import asyncio
import random
import logging
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from sqlalchemy.exc import SQLAlchemyError

from app.models.quiz import Option, Question, Quiz, QuizTrend, UserActivity, QuizAttempt
from app.models.user import User
from app.models.database import get_db
from app.utils.groq_client import GroqClient
from config import settings

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2


async def async_sleep(seconds: float):
    await asyncio.sleep(seconds)


class AIAgentService:
    def __init__(self):
        self.groq_client = GroqClient()
        self.technologies = settings.TOP_TECHNOLOGIES
        self.delay_minutes = 30
        self._running = False
        self.last_activity = "Not started yet"
        # print(f"Agent initialized with technologies: {self.technologies}")

    async def run_scheduled_generation(self):
        self._running = True
        logger.info(
            f"Starting generation loop (interval: {self.delay_minutes} mins)"
        )

        while self._running:
            try:
                start_time = datetime.now(timezone.utc)
                logger.info("Starting quiz generation")
                await self.generate_trending_quiz()
                self.last_activity = datetime.now(timezone.utc)
                duration = (self.last_activity - start_time).total_seconds()
                logger.info(f"Generated quiz in {duration:.2f}s")
            except Exception as e:
                logger.error(f"Generation failed: {e}")
            finally:
                logger.info(f"⏳ Next run in {self.delay_minutes} minutes")
                await asyncio.sleep(self.delay_minutes * 60)

    async def stop(self):
        self._running = False

    async def generate_trending_quiz(self):
        db = next(get_db())
        try:
            technology = random.choice(self.technologies)
            difficulty = random.choice(["easy", "medium", "hard"])
            num_questions = random.randint(15, 25)

            logger.info(f"Attempting to generate quiz: {technology} ({difficulty})")

            quiz_data = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    quiz_data = await self.groq_client.generate_quiz(
                        technology=technology,
                        difficulty=difficulty,
                        num_questions=num_questions,
                    )
                    if quiz_data:
                        logger.info(f"Quiz generated on attempt {attempt}")
                        break
                except Exception as e:
                    logger.warning(f"Groq API failed (Attempt {attempt}): {e}")

                backoff = INITIAL_BACKOFF_SECONDS * 2 ** (attempt - 1)
                logger.info(f"⏳ Retrying in {backoff}s...")
                await async_sleep(backoff)

            if not quiz_data:
                logger.error("All retries failed. Could not generate quiz.")
                return

            quiz = Quiz(
                title=quiz_data["title"],
                description=quiz_data.get("description", ""),
                technology=technology,
                difficulty=difficulty,
                num_questions=num_questions,
                created_by=-1,
                is_public=True,
                is_ai_generated=True,
                created_at=datetime.now(timezone.utc),
            )

            db.add(quiz)
            db.commit()
            db.refresh(quiz)

            for q in quiz_data["questions"]:
                question = Question(
                    quiz_id=quiz.id,
                    question_text=q["question_text"],
                    explanation=q.get("explanation", ""),
                    created_at=datetime.now(timezone.utc),
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
            logger.info(f"Successfully created quiz ID: {quiz.id}")
            self.update_trends(db, technology)

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"DB error during quiz creation: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during quiz generation: {e}")
        finally:
            db.close()


    def update_trends(self, db: Session, technology: str):
        try:
            trend = (
                db.query(QuizTrend).filter(QuizTrend.technology == technology).first()
            )
            if trend:
                trend.popularity_score = trend.popularity_score + 1.0
                trend.last_updated = func.now()
            else:
                trend = QuizTrend(
                    technology=technology, popularity_score=1.0, last_updated=func.now()
                )
                db.add(trend)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating trends: {e}")

    async def analyze_user_behavior(self, user_id: int, quiz_id: int):
        db = next(get_db())
        try:
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if not quiz:
                return

            activity = (
                db.query(UserActivity)
                .filter(
                    UserActivity.user_id == user_id,
                    UserActivity.technology == quiz.technology,
                )
                .first()
            )

            if activity:
                activity.interaction_score += 1.0
                activity.last_interaction = func.now()
            else:
                activity = UserActivity(
                    user_id=user_id, technology=quiz.technology, interaction_score=1.0
                )
                db.add(activity)

            db.commit()
            self.update_trends(db, quiz.technology)

        except Exception as e:
            db.rollback()
            logger.error(f"Error analyzing user behavior: {e}")
        finally:
            db.close()

    async def get_recommendations(self, user_id: int) -> List[Dict]:
        db = next(get_db())
        try:
            user_techs = (
                db.query(UserActivity.technology)
                .filter(UserActivity.user_id == user_id)
                .order_by(UserActivity.interaction_score.desc())
                .limit(3)
                .all()
            )

            tech_list = [tech[0] for tech in user_techs] if user_techs else []

            if not tech_list:
                trend_techs = (
                    db.query(QuizTrend.technology)
                    .order_by(QuizTrend.popularity_score.desc())
                    .limit(3)
                    .all()
                )
                tech_list = [tech[0] for tech in trend_techs]

            quizzes_query = db.query(Quiz).filter(Quiz.is_public == True)

            if tech_list:
                quizzes_query = quizzes_query.filter(Quiz.technology.in_(tech_list))

            quizzes = quizzes_query.order_by(Quiz.created_at.desc()).all()

            # Deduplicate and shuffle to avoid showing same technology repeatedly
            seen_ids = set()
            unique_quizzes = []
            for quiz in quizzes:
                if quiz.id not in seen_ids:
                    seen_ids.add(quiz.id)
                    unique_quizzes.append(quiz)

            random.shuffle(unique_quizzes)
            selected = unique_quizzes[:15]

            return [
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "technology": quiz.technology,
                    "difficulty": quiz.difficulty,
                }
                for quiz in selected
            ]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
        finally:
            db.close()

    async def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        db = next(get_db())
        try:
            results = (
                db.query(
                    User.username,
                    func.coalesce(func.sum(QuizAttempt.score), 0).label("total_score"),
                )
                .join(User, QuizAttempt.user_id == User.id)
                .group_by(User.id, User.username)
                .order_by(desc("total_score"))
                .limit(limit)
                .all()
            )

            return [
                {
                    "username": row.username,
                    "total_score": int(row.total_score),
                    "rank": idx + 1,
                }
                for idx, row in enumerate(results)
            ]
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
        finally:
            db.close()
