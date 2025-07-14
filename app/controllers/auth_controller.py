from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserInDB
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.dependencies import get_current_user

router = APIRouter()
auth_service = AuthService()
user_service = UserService()

@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return user_service.create_user(db=db, user=user)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    return auth_service.login_user(db, form_data.username, form_data.password)

@router.get("/me", response_model=UserInDB)
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return current_user
