from fastapi import APIRouter, Depends, HTTPException, status
from mysql.connector import MySQLConnection
from datetime import timedelta

from ...schemas.user import UserCreate, UserLogin, Token, UserResponse
from ...models.user import create_user, get_user_by_username, get_user_by_id
from ...core.database import get_db
from ...core.security import verify_password, create_access_token
from ...core.config import settings
from ...api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, conn: MySQLConnection = Depends(get_db)):
    existing = get_user_by_username(conn, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    try:
        user_id = create_user(conn, user.model_dump())
        new_user = get_user_by_id(conn, user_id)
        return UserResponse(**new_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, conn: MySQLConnection = Depends(get_db)):
    user = get_user_by_username(conn, user_data.username)
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(access_token=access_token)

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return UserResponse(**current_user)