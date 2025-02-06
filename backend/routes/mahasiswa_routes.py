from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from pydantic import BaseModel, EmailStr
from model.mahasiswa_model import Mahasiswa
from model.user_model import User  # Import the User model

router = APIRouter()

# Pydantic Models
class MahasiswaBase(BaseModel):
    program_studi_id: int
    tahun_masuk: int
    semester: int
    sks_diambil: int
    user_id: int
    nama: str
    tgl_lahir: date
    kota_lahir: str
    jenis_kelamin: str
    kewarganegaraan: str
    alamat: str
    kode_pos: Optional[int] = None
    hp: str
    email: EmailStr
    nama_ayah: Optional[str] = None
    nama_ibu: Optional[str] = None
    pekerjaan_ayah: Optional[str] = None
    pekerjaan_ibu: Optional[str] = None
    status_kawin: Optional[bool] = False

class MahasiswaUpdate(BaseModel):
    program_studi_id: Optional[int] = None
    tahun_masuk: Optional[int] = None
    semester: Optional[int] = None
    sks_diambil: Optional[int] = None
    nama: Optional[str] = None
    tgl_lahir: Optional[date] = None
    kota_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    kewarganegaraan: Optional[str] = None
    alamat: Optional[str] = None
    kode_pos: Optional[int] = None
    hp: Optional[str] = None
    email: Optional[EmailStr] = None
    nama_ayah: Optional[str] = None
    nama_ibu: Optional[str] = None
    pekerjaan_ayah: Optional[str] = None
    pekerjaan_ibu: Optional[str] = None
    status_kawin: Optional[bool] = False

class MahasiswaCreate(MahasiswaBase):
    pass

class MahasiswaRead(MahasiswaBase):
    id: int

    class Config:
        orm_mode = True

# Create Mahasiswa
@router.post("/", response_model=MahasiswaRead, status_code=status.HTTP_201_CREATED)
async def create_mahasiswa(mahasiswa: MahasiswaCreate, db: Session = Depends(get_db)):
    # Check if the User exists
    user = db.query(User).filter(User.id == mahasiswa.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with the given user_id not found")

    # Check if a Mahasiswa with the same user_id already exists
    existing_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.user_id == mahasiswa.user_id).first()
    if existing_mahasiswa:
        raise HTTPException(status_code=400, detail="A Mahasiswa with this user_id already exists")

    # Create and save the Mahasiswa
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
async def update_mahasiswa(mahasiswa_id: int, mahasiswa: MahasiswaUpdate, db: Session = Depends(get_db)):
    db_mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not db_mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # Ensure the User exists
    user = db.query(User).filter(User.id == db_mahasiswa.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with the given user_id not found")

    for key, value in mahasiswa.dict(exclude_unset=True).items():
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