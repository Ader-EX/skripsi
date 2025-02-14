from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, validator

from database import get_db
from model.dosen_model import Dosen
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.user_model import User

# Updated models to match your schema
class UserRead(BaseModel):
    id: int
    nim_nip: str
    role: str

    class Config:
        orm_mode = True

class DosenBase(BaseModel):
    nidn: Optional[str]
    pegawai_id: Optional[int]
    nomor_ktp: Optional[str]
    email: Optional[EmailStr]
    progdi_id: Optional[int]
    tanggal_lahir: datetime
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    
    user_id: int

    @validator("tanggal_lahir", pre=True)
    def parse_tanggal_lahir(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("tanggal_lahir must be in the format DD/MM/YYYY")

class DosenCreate(DosenBase):
    pass

class DosenRead(BaseModel):
    pegawai_id: int
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    email: Optional[str]
    progdi_id: Optional[int]
    tanggal_lahir: Optional[str]
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    
    user: UserRead

    class Config:
        orm_mode = True

    @validator("tanggal_lahir", pre=True)
    def format_tanggal_lahir(cls, value):
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")
        return value

class DosenUpdate(BaseModel):
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    email: Optional[EmailStr]
    progdi_id: Optional[int]
    tanggal_lahir: Optional[date]
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    

router = APIRouter()

@router.get("/dashboard-stats/{dosen_id}", response_model=Dict[str, Any])
async def get_dashboard_stats(dosen_id: int, db: Session = Depends(get_db)):
    # Get count of mata kuliah
    mata_kuliah_count = db.query(func.count(MataKuliah.kodemk)).scalar()
    
    # Get count of ruangan
    ruangan_count = db.query(func.count(Ruangan.id)).scalar()
    
    # Get count of classes assigned to this dosen
    classes_taught = db.query(func.count(OpenedClass.id))\
        .join(OpenedClass.dosens)\
        .filter(Dosen.pegawai_id == dosen_id)\
        .scalar()

    return {
        "mata_kuliah": {
            "count": mata_kuliah_count,
            "label": "Jumlah Mata Kuliah"
        },
        "ruangan": {
            "count": ruangan_count,
            "label": "Jumlah Ruangan Terdaftar"
        },
        "classes_taught": {
            "count": classes_taught,
            "label": "Mata Kuliah yang Diajar"
        }
    }

@router.get("/get-all", response_model=Dict[str, Any])
async def get_all_dosen(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    query = db.query(Dosen).join(User).options(joinedload(Dosen.user))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.nim_nip.ilike(search_pattern),
                Dosen.nidn.ilike(search_pattern),
                Dosen.email.ilike(search_pattern)
            )
        )

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    dosens = query.offset((page - 1) * limit).limit(limit).all()

    formatted_dosens = [
        {
            "pegawai_id": dosen.pegawai_id,
            "nidn": dosen.nidn,
            "nomor_ktp": dosen.nomor_ktp,
            "email": dosen.email,
            "progdi_id": dosen.progdi_id,
            "tanggal_lahir": dosen.tanggal_lahir.strftime("%d/%m/%Y") if dosen.tanggal_lahir else None,
            "ijin_mengajar": dosen.ijin_mengajar,
            "jabatan": dosen.jabatan,
            "title_depan": dosen.title_depan,
            "title_belakang": dosen.title_belakang,
            "jabatan_id": dosen.jabatan_id,
            "is_sekdos": dosen.is_sekdos,
            
            "user": {
                "id": dosen.user.id,
                "nim_nip": dosen.user.nim_nip,
                "role": dosen.user.role
            }
        }
        for dosen in dosens
    ]

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": formatted_dosens
    }

@router.post("/", response_model=DosenRead)
async def create_dosen(dosen: DosenCreate = Body(...), db: Session = Depends(get_db)):
    dosen_data = dosen.dict()
    dosen_data["tanggal_lahir"] = (
        dosen.tanggal_lahir if isinstance(dosen.tanggal_lahir, datetime) else None
    )

    db_dosen = Dosen(**dosen_data)
    db.add(db_dosen)
    db.commit()
    db.refresh(db_dosen)
    return db_dosen

@router.get("/{dosen_id}", response_model=DosenRead)
async def get_dosen(dosen_id: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")
    return dosen

@router.put("/{dosen_id}", response_model=DosenRead)
async def update_dosen(dosen_id: int, dosen: DosenUpdate, db: Session = Depends(get_db)):
    db_dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not db_dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    update_data = dosen.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dosen, key, value)

    db.commit()
    db.refresh(db_dosen)
    return db_dosen

@router.get("/get-dosen/names", response_model=Dict[str, Any])
async def get_dosen_names(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter: Optional[str] = Query(None)
):
    query = db.query(Dosen.pegawai_id, Dosen.nama).join(User)

    if filter:
        query = query.filter(Dosen.nama.ilike(f"%{filter}%"))

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    dosen_names = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [{"id": dosen.pegawai_id, "nama": dosen.nama} for dosen in dosen_names]
    }