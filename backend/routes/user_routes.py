from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from model.user_model import User
from pydantic import BaseModel


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)
router = APIRouter()


# Pydantic model for validation
class UserCreate(BaseModel):
    fullname: str
    email: str
    password: str
    role: str

class UserRead(BaseModel):
    id: int
    fullname: str
    email: str
    role: str

    class Config:
        orm_mode = True

@router.post("/users", response_model=UserRead,status_code=status.HTTP_201_CREATED)
async def create_user(user : UserCreate, db: Session = Depends(get_db)):
    if user.role not in {"mahasiswa", "dosen", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Check if the user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create the user
    new_user = User(
        fullname=user.fullname,
        email=user.email,
        password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user