from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from model.dosen_model import  Dosen
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DosenBase(BaseModel):
    nidn: Optional[str]
    nip: Optional[str]
    nomor_ktp: Optional[str]
    nama: str
    tanggal_lahir: Optional[datetime]
    progdi_id: str
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    is_dosen_kb: Optional[bool] = False
    user_id: int


class DosenCreate(DosenBase):
    pass

class DosenRead(DosenBase):
    id : int
    class Config:
        orm_mode  = True

router = APIRouter()

@router.post("/dosen", response_model=DosenRead, status_code=status.HTTP_201_CREATED)
async def create_dosen(dosen = DosenCreate, db : Session = Depends(get_db)):
    db_dosen = Dosen(**dosen.dict())
    db.add(db_dosen)
    db.commit()
    db.refresh(db_dosen)
    return db_dosen


@router.get("/dosen/{dosen_id}", response_model=DosenRead, status_code=status.HTTP_200_OK)
def get_dosen(dosen_id : int, db : Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen


@router.get("/dosen", response_model=List[DosenRead])
async def get_all_dosen(db : Session = Depends(get_db)):
    dosen = db.query(Dosen).all()
    return dosen