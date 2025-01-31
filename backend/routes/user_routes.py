from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from model.user_model import User
from pydantic import BaseModel
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from jwt import encode, decode
from datetime import datetime, timedelta, timezone
from enum import Enum  # Import Enum for predefined options

# Load environment variables from .env file
load_dotenv()

# Get configurations from .env
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


# Enum for Role Options
class RoleEnum(str, Enum):
    mahasiswa = "mahasiswa"
    dosen = "dosen"
    admin = "admin"


# Utility functions for password hashing and JWT
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Pydantic models
class UserCreate(BaseModel):
    fullname: str
    email: str
    password: str
    role: RoleEnum  # Use Enum for predefined options


class UserRead(BaseModel):
    id: int
    fullname: str
    email: str
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Routes
@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    new_user = User(
        fullname=user.fullname,
        email=user.email,
        password=hashed_password,
        role=user.role.value,  # Get the string value of the Enum
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users", response_model=List[UserRead])
async def get_all_users(role: Optional[RoleEnum] = Query(None, description="Filter users by role"),
                        db: Session = Depends(get_db)):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.value)
    users = query.all()
    return users

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(user_id: int, updated_user: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.fullname = updated_user.fullname
    user.email = updated_user.email
    user.password = hash_password(updated_user.password)
    user.role = updated_user.role.value
    db.commit()
    db.refresh(user)
    return user


class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/token", response_model=Token)
async def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_request.email).first()
    if not user or not verify_password(login_request.password, user.password):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}