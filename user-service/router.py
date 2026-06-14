from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import os

from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse, UserSummary

load_dotenv()

router = APIRouter(prefix="/v1/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        or_(User.email == user_data.email, User.username == user_data.username)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email lub nazwa użytkownika już zajęta")

    hashed_password = pwd_context.hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/all", response_model=List[UserSummary])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.enabled == True).all()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/search", response_model=List[UserSummary])
def search_users(query: str, db: Session = Depends(get_db)):
    results = db.query(User).filter(
        or_(
            User.username.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%"),
        )
    ).all()
    return results


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    return user


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user