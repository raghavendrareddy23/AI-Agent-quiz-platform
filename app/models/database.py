from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config import settings
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    engine = create_engine(settings.DATABASE_URL, echo=False, future=True)
    logger.info("Database connection established.")
except Exception as e:
    logger.error(f"Database connection failed: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
