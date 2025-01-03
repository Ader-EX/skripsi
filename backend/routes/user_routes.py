from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..model.user_model import User
from pydantic import BaseModel

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

@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if user.role not in {"mahasiswa", "dosen", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
