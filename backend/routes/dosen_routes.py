from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, validator

from model.temporary_timetable_model import TemporaryTimeTable
from model.academicperiod_model import AcademicPeriods
from model.timeslot_model import TimeSlot
from model.timetable_model import TimeTable
from database import get_db
from model.dosen_model import Dosen
from model.programstudi_model import ProgramStudi
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.user_model import User

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRead(BaseModel):
    id: int
    nim_nip: str
    role: str

    class Config:
        orm_mode = True


class DosenCreate(BaseModel):
    nim_nip: str
    password: str
    nama: str
    email: EmailStr
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    tanggal_lahir: str
    progdi_id: Optional[int]
    status_dosen: Optional[str]
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]

class DosenBase(BaseModel):
    nim_nip: str
    password: str
    nama: str
    email: EmailStr
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    tanggal_lahir: str
    progdi_id: Optional[int]
    status_dosen: Optional[str]
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    user_id: Optional[int] 

    @validator("tanggal_lahir", pre=True)
    def parse_tanggal_lahir(cls, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise ValueError("tanggal_lahir harus dengan format DD/MM/YYYY")


class DosenRead(BaseModel):
    pegawai_id: int
    nidn: Optional[str]
    nomor_ktp: Optional[str]
    email: Optional[str]
    nama: str
    progdi_id: Optional[int]
    tanggal_lahir: Optional[str]
    status_dosen: Optional[str]
    jabatan: Optional[str]
    title_depan: Optional[str]
    title_belakang: Optional[str]
    user: UserRead  

    class Config:
        orm_mode = True

    @validator("tanggal_lahir", pre=True)
    def format_tanggal_lahir(cls, value):
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y")
        return value



router = APIRouter()


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
                Dosen.email.ilike(search_pattern),
                Dosen.nama.ilike(search_pattern)
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
            "nama": dosen.nama,
            "progdi_id": dosen.progdi_id,
            "tanggal_lahir": dosen.tanggal_lahir.strftime("%d/%m/%Y") if dosen.tanggal_lahir else None,
            "status_dosen": dosen.status_dosen,
            "jabatan": dosen.jabatan,
            "title_depan": dosen.title_depan,
            "title_belakang": dosen.title_belakang,
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



@router.post("/", response_model=dict)
async def create_dosen(dosen: DosenCreate = Body(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.nim_nip == dosen.nim_nip).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User dengan NIM/NIP ini sudah ada.")

    new_user = User(
        nim_nip=dosen.nim_nip,
        password=dosen.password,
        role="dosen"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    new_dosen = Dosen(
        user_id=new_user.id,
        nama=dosen.nama,
        email=dosen.email,
        nidn=dosen.nidn,
        nomor_ktp=dosen.nomor_ktp,
        tanggal_lahir=datetime.strptime(dosen.tanggal_lahir, "%Y-%m-%d"),
        progdi_id=dosen.progdi_id,
        status_dosen=dosen.status_dosen,
        jabatan=dosen.jabatan,
        title_depan=dosen.title_depan,
        title_belakang=dosen.title_belakang
    )
    db.add(new_dosen)
    db.commit()
    db.refresh(new_dosen)

    return {"message": "Dosen berhasil ditambahkan", "dosen_id": new_dosen.pegawai_id}


@router.get("/dashboard-stats/{dosen_id}", response_model=Dict[str, Any])
async def get_dashboard_stats(dosen_id: int, db: Session = Depends(get_db)):
    mata_kuliah_count = db.query(func.count(MataKuliah.kodemk)).scalar()
    
    ruangan_count = db.query(func.count(Ruangan.id)).scalar()
    
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

@router.get("/{dosen_id}", response_model=DosenRead)
async def get_dosen(dosen_id: int, db: Session = Depends(get_db)):
    dosen = db.query(Dosen).options(joinedload(Dosen.user)).filter(Dosen.pegawai_id == dosen_id).first()
    
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    return dosen





class DosenUpdate(BaseModel):
    nim_nip: Optional[str] = None
    password: Optional[str] = None
    nama: Optional[str] = None
    nidn: Optional[str] = None
    nomor_ktp: Optional[str] = None
    tanggal_lahir: Optional[str] = None 
    progdi_id: Optional[int] = None
    status_dosen: Optional[str] = None
    jabatan: Optional[str] = None
    title_depan: Optional[str] = None
    title_belakang: Optional[str] = None
    email: Optional[str] = None
    
@router.put("/{dosen_id}", response_model=dict)
async def update_dosen(dosen_id: int, dosen: DosenUpdate, db: Session = Depends(get_db)):
    db_dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not db_dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    db_user = db.query(User).filter(User.id == db_dosen.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User relasinya tidak ditemukan")

    if dosen.nim_nip is not None:
        db_user.nim_nip = dosen.nim_nip
        
    if dosen.password:
        hashed_password = pwd_context.hash(dosen.password)
        db_user.password = hashed_password

    if dosen.nama is not None:
        db_dosen.nama = dosen.nama
    if dosen.email is not None:
        db_dosen.email = dosen.email
    if dosen.nidn is not None:
        db_dosen.nidn = dosen.nidn
    if dosen.nomor_ktp is not None:
        db_dosen.nomor_ktp = dosen.nomor_ktp
    if dosen.tanggal_lahir:
        db_dosen.tanggal_lahir = datetime.strptime(dosen.tanggal_lahir, "%Y-%m-%d")
    if dosen.progdi_id is not None:
        db_dosen.progdi_id = dosen.progdi_id
    if dosen.status_dosen is not None:
        db_dosen.status_dosen = dosen.status_dosen
    if dosen.jabatan is not None:
        db_dosen.jabatan = dosen.jabatan
    if dosen.title_depan is not None:
        db_dosen.title_depan = dosen.title_depan
    if dosen.title_belakang is not None:
        db_dosen.title_belakang = dosen.title_belakang

    db.commit()
    db.refresh(db_dosen)
    db.refresh(db_user)

    return {"message": "Dosen berhasil diperbarui", "dosen_id": db_dosen.pegawai_id} 

@router.get("/timetable/{dosen_id}", response_model=Dict[str, Any])
async def get_timetable_by_dosen(
    dosen_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk"),
    prodi_id : Optional[int] = Query(None, description="Filter by Prodi ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    try:
        query = db.query(
        TimeTable.id.label("timetable_id"),
        ProgramStudi.id.label("program_studi_id"),
        TimeTable.opened_class_id,
        TimeTable.ruangan_id,
        TimeTable.timeslot_ids,
        TimeTable.kelas,
        TimeTable.kapasitas,
        TimeTable.kuota,
        OpenedClass.mata_kuliah_kodemk,
        MataKuliah.kodemk,
        MataKuliah.namamk,
        MataKuliah.kurikulum,
        MataKuliah.sks,
        MataKuliah.smt,
        Ruangan.nama_ruang.label("ruangan_name"),
        func.group_concat(
            func.concat_ws(" ", Dosen.title_depan, Dosen.nama, Dosen.title_belakang)
            .distinct()
            .op('SEPARATOR')('||')
        ).label("dosen_names"),
            case(
            (TemporaryTimeTable.id.isnot(None), True),
            else_=False
        )
        .label("has_temporary") 
    ).join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
    .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk) \
    .join(ProgramStudi, MataKuliah.program_studi_id == ProgramStudi.id) \
    .join(Dosen, OpenedClass.dosens) \
    .join(User, Dosen.user_id == User.id) \
    .join(Ruangan, TimeTable.ruangan_id == Ruangan.id) \
    .join(AcademicPeriods, TimeTable.academic_period_id == AcademicPeriods.id) \
    .outerjoin(TemporaryTimeTable, TimeTable.id == TemporaryTimeTable.timetable_id) \
    .filter(
        and_(
            OpenedClass.dosens.any(Dosen.pegawai_id == dosen_id),
            AcademicPeriods.is_active == True
        )
    ) \
    .group_by(
        TimeTable.id,
        OpenedClass.id,
        MataKuliah.kodemk,
        MataKuliah.namamk,
        MataKuliah.kurikulum,
        MataKuliah.sks,
        MataKuliah.smt,
        Ruangan.nama_ruang,
        ProgramStudi.id,
        TemporaryTimeTable.id
    )

        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )
            
        if prodi_id is not None and prodi_id != 0:
            query = query.filter(ProgramStudi.id == prodi_id)

   
        total_records = query.count()
        total_pages = (total_records + page_size - 1) // page_size

        timetable_data = query.offset((page - 1) * page_size).limit(page_size).all()

        timeslot_ids = set(
            ts_id for entry in timetable_data for ts_id in entry.timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        formatted_timetable = []
        for entry in timetable_data:
           
            formatted_dosen = (
                "\n".join(
                    [f"{i+1}. {name.strip()}" for i, name in enumerate(entry.dosen_names.split("||"))]
                )
                if entry.dosen_names else "-"
            )
            
            formatted_timeslots = [
                {
                    "id": ts.id,
                    "day": ts.day,
                    "start_time": ts.start_time.strftime("%H:%M:%S"),
                    "end_time": ts.end_time.strftime("%H:%M:%S"),
                }
                for ts_id in entry.timeslot_ids if (ts := timeslot_map.get(ts_id))
            ]

            if formatted_timeslots:
                sorted_slots = sorted(formatted_timeslots, key=lambda x: x["start_time"])
                day = sorted_slots[0]["day"]
                schedule = f"{day}\t{sorted_slots[0]['start_time']} - {sorted_slots[-1]['end_time']}"
            else:
                schedule = "-"

            formatted_entry = {
                "timetable_id": entry.timetable_id,
                "kodemk": entry.kodemk,
                "course_id" : entry.opened_class_id,
                "matakuliah": entry.namamk,
                "kurikulum": entry.kurikulum,
                "kelas": entry.kelas,
                "kap_peserta": f"{entry.kapasitas} / {entry.kuota}",
                "sks": entry.sks,
                "smt": entry.smt,
                "dosen": formatted_dosen,
                "ruangan": entry.ruangan_name,
                "schedule": schedule,  
                "has_temporary": entry.has_temporary,
                
            }
            formatted_timetable.append(formatted_entry)

        return {
            "dosen_id": dosen_id,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": formatted_timetable,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{dosen_id}", response_model=dict)
async def delete_dosen(dosen_id: int, db: Session = Depends(get_db)):

    db_dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not db_dosen:
        raise HTTPException(status_code=404, detail="Dosen tidak ditemukan")

    db_user = db.query(User).filter(User.id == db_dosen.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Associated User tidak ditemukan")

    db.delete(db_dosen)
    db.commit()

    db.delete(db_user)
    db.commit()

    return {"message": "Dosen dan User berhasil dihapus"}
