from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.token import Token
from app.utils.security import create_access_token
from config import settings
from app.services.user_service import UserService

user_service = UserService()

class AuthService:
    def login_user(self, db: Session, username: str, password: str) -> Token:
        user = user_service.authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")
