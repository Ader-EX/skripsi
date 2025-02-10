from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, or_
from sqlalchemy.orm import Session,joinedload
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.user_model import User
from database import get_db
from model.dosen_model import Dosen
from datetime import date, datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, EmailStr, validator, field_validator

class UserRead(BaseModel):
    id: int
    fullname: str
    email: EmailStr

    class Config:
        orm_mode = True

class DosenBase(BaseModel):
    nidn: Optional[str]
    pegawai_id: Optional[int]
    nip: Optional[str]
    nomor_ktp: Optional[str]
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


class DosenRead(BaseModel):
    id: int
    nidn: Optional[str]
    pegawai_id: Optional[int]
    nip: Optional[str]
    nomor_ktp: Optional[str]
    progdi_id: Optional[int]
    tanggal_lahir: Optional[str]
    ijin_mengajar: Optional[bool] = True
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    jabatan_id: Optional[int]
    is_sekdos: Optional[bool] = False
    is_dosen_kb: Optional[bool] = False
    user: UserRead  # ✅ Get fullname from User

    class Config:
        orm_mode = True

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



@router.get("/dashboard-stats/{dosen_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_dashboard_stats(dosen_id: int, db: Session = Depends(get_db)):
    # Get count of mata kuliah
    mata_kuliah_count = db.query(func.count(MataKuliah.kodemk)).scalar()
    
    # Get count of ruangan
    ruangan_count = db.query(func.count(Ruangan.id)).scalar()
    
    # Get count of classes assigned to this dosen
    classes_taught = db.query(func.count(OpenedClass.id))\
        .join(OpenedClass.dosens)\
        .filter(Dosen.id == dosen_id)\
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


@router.get("/get-all", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_all_dosen(
    db: Session = Depends(get_db),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(10, description="Items per page", ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by fullname, email, or NIDN")
):
    query = db.query(Dosen).join(User).options(
        joinedload(Dosen.user)  # ✅ Ensure user data is loaded
    )

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.fullname.ilike(search_pattern),  
                User.email.ilike(search_pattern),
                Dosen.nidn.ilike(search_pattern)  # ✅ Now searchable by NIDN
            )
        )

    # ✅ Get total records before pagination
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    # ✅ Apply pagination
    dosens = query.offset((page - 1) * limit).limit(limit).all()

    # ✅ Format tanggal_lahir properly
    formatted_dosens = [
        {
            "id": dosen.id,
            "nidn": dosen.nidn,
            "pegawai_id": dosen.pegawai_id,
            "nip": dosen.nip,
            "nomor_ktp": dosen.nomor_ktp,
            "progdi_id": dosen.progdi_id,
            "tanggal_lahir": dosen.tanggal_lahir.strftime("%d/%m/%Y") if dosen.tanggal_lahir else None,
            "ijin_mengajar": dosen.ijin_mengajar,
            "jabatan": dosen.jabatan,
            "title_depan": dosen.title_depan,
            "title_belakang": dosen.title_belakang,
            "jabatan_id": dosen.jabatan_id,
            "is_sekdos": dosen.is_sekdos,
            "is_dosen_kb": dosen.is_dosen_kb,
            "user": {
                "id": dosen.user.id,
                "fullname": dosen.user.fullname,
                "email": dosen.user.email
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

@router.post("/", response_model=DosenRead, status_code=status.HTTP_201_CREATED)
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

@router.get("/get-dosen/names", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_dosen_names(
    db: Session = Depends(get_db),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Number of items per page", ge=1, le=100),
    filter: Optional[str] = Query(None, description="Filter by name or ID")
):
    query = db.query(Dosen.id, User.fullname).join(User)

    if filter:
        try:
            filter_id = int(filter)
            query = query.filter(
                or_(
                    User.fullname.ilike(f"%{filter}%"),  
                    Dosen.id == filter_id
                )
            )
        except ValueError:
            query = query.filter(User.fullname.ilike(f"%{filter}%"))

    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit

    dosen_names = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "total_records": total_records,
        "data": [{"id": dosen.id, "nama": dosen.fullname} for dosen in dosen_names]
    }
