from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from model.user_model import User
from database import get_db
from model.dosen_model import Dosen
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, validator, field_validator



class DosenBase(BaseModel):
    nidn: Optional[str]
    pegawai_id: Optional[int]
    nip: Optional[str]
    nomor_ktp: Optional[str]
    nama: str
    progdi_id: Optional[int]
    tanggal_lahir: datetime
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    is_dosen_kb: Optional[bool] = False
    user_id: int

    @validator("tanggal_lahir", pre=True, always=True)
    def parse_tanggal_lahir(cls, value):
        if value is None:
            return None
        try:
            # Parse the date from "day/month/year" format
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("tanggal_lahir must be in the format DD/MM/YYYY")


class DosenCreate(DosenBase):
    pass


class DosenRead(DosenBase):
    id: int

    @validator("tanggal_lahir", pre=True, always=True)
    def format_tanggal_lahir(cls, value):
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")
        return value

    class Config:
        orm_mode = True


class DosenUpdate(BaseModel):
    nidn: Optional[str]
    pegawai_id: Optional[int]
    nip: Optional[str]
    nomor_ktp: Optional[str]
    nama: str
    progdi_id: Optional[int]
    tanggal_lahir: Optional[date]
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    is_dosen_kb: Optional[bool] = False
    

router = APIRouter()


@router.post("/dosen", response_model=DosenRead, status_code=status.HTTP_201_CREATED)
async def create_dosen(dosen: DosenCreate = Body(...), db: Session = Depends(get_db)):
    # Ensure tanggal_lahir is a datetime object before storing in the database
    dosen_data = dosen.dict()
    dosen_data["tanggal_lahir"] = (
        dosen.tanggal_lahir if isinstance(dosen.tanggal_lahir, datetime) else None
    )

    db_dosen = Dosen(**dosen_data)
    db.add(db_dosen)
    db.commit()
    db.refresh(db_dosen)
    return db_dosen


@router.get("/{dosen_id}", response_model=DosenRead, status_code=status.HTTP_200_OK)
async def get_dosen(dosen_id: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen


@router.get("/dosen", response_model=List[DosenRead], status_code=status.HTTP_200_OK)
async def get_all_dosen(db: Session = Depends(get_db)):
    dosen = db.query(Dosen).all()
    return dosen

@router.put("/{dosen_id}", response_model=DosenRead)
async def update_dosen(dosen_id: int, dosen: DosenUpdate, db: Session = Depends(get_db)):
    db_dosen = db.query(Dosen).filter(Dosen.id == dosen_id).first()
    if not db_dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    # Exclude 'id' and 'user_id' from being updated
    update_data = dosen.dict(exclude_unset=True, exclude={"user_id", "id"})

    for key, value in update_data.items():
        setattr(db_dosen, key, value)

    db.commit()
    db.refresh(db_dosen)
    return db_dosen

