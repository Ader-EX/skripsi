from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from pydantic import BaseModel

from model.mahasiswa_model import Mahasiswa

router = APIRouter()

# Pydantic Models
class MahasiswaBase(BaseModel):
    program_studi: str
    tahun_masuk: int
    semester: int
    sks_diambil: int
    user_id: int

class MahasiswaCreate(MahasiswaBase):
    pass

class MahasiswaRead(MahasiswaBase):
    id: int

    class Config:
        orm_mode = True


# Create Mahasiswa
@router.post("/", response_model=MahasiswaRead, status_code=status.HTTP_201_CREATED)
async def create_mahasiswa(mahasiswa: MahasiswaCreate, db: Session = Depends(get_db)):
    db_mahasiswa = Mahasiswa(**mahasiswa.dict())
    db.add(db_mahasiswa)
    db.commit()
    db.refresh(db_mahasiswa)
    return db_mahasiswa


# Read Mahasiswa by ID
@router.get("/{mahasiswa_id}", response_model=MahasiswaRead)
async def read_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")
    return db_mahasiswa


# Read All Mahasiswa
@router.get("/", response_model=List[MahasiswaRead])
async def read_all_mahasiswa(db: Session = Depends(get_db)):
    return db.query(Mahasiswa).all()


# Update Mahasiswa
@router.put("/{mahasiswa_id}", response_model=MahasiswaRead)
async def update_mahasiswa(mahasiswa_id: int, mahasiswa: MahasiswaCreate, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    for key, value in mahasiswa.dict().items():
        setattr(db_mahasiswa, key, value)

    db.commit()
    db.refresh(db_mahasiswa)
    return db_mahasiswa


# Delete Mahasiswa
@router.delete("/{mahasiswa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    db.delete(db_mahasiswa)
    db.commit()
    return {"message": "Mahasiswa deleted successfully"}
