from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, Optional, List
from datetime import datetime
from model.academicperiod_model import AcademicPeriods
from model.mahasiswa_model import Mahasiswa
from model.mahasiswatimetable_model import MahasiswaTimeTable
from model.timeslot_model import TimeSlot
from model.dosen_model import Dosen
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.timetable_model import TimeTable
from model.user_model import User
from database import get_db 
from model.temporary_timetable_model import TemporaryTimeTable

router = APIRouter()

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TemporaryTimeTableBase(BaseModel):
    timetable_id: int
    academic_period_id: int  
    new_ruangan_id: Optional[int] = None
    new_timeslot_ids: Optional[List[int]] = None
    new_day: Optional[str] = None
    change_reason: Optional[str] = None
    start_date: datetime
    end_date: datetime
    created_by: Optional[str] = None

class TemporaryTimeTableCreate(TemporaryTimeTableBase):
    pass

class TemporaryTimeTableUpdate(BaseModel):
    academic_period_id: Optional[int] = None 
    new_ruangan_id: Optional[int] = None
    new_timeslot_ids: Optional[List[int]] = None
    new_day: Optional[str] = None
    change_reason: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None

class TemporaryTimeTableResponse(TemporaryTimeTableBase):
    id: int

    class Config:
        orm_mode = True



def create_temporary_timetable(db: Session, temp_data: TemporaryTimeTableCreate):
    
    academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == temp_data.academic_period_id).first()
    if not academic_period:
        raise HTTPException(status_code=404, detail="Academic period tidak ditemukan")

    db_temp = TemporaryTimeTable(**temp_data.dict())
    db.add(db_temp)
    db.commit()
    db.refresh(db_temp)
    return db_temp

def get_all_temporary_timetables(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TemporaryTimeTable).offset(skip).limit(limit).all()

def get_temporary_timetable_by_id(db: Session, temp_id: int):
    return db.query(TemporaryTimeTable).filter(TemporaryTimeTable.id == temp_id).first()

def update_temporary_timetable(db: Session, temp_id: int, temp_data: TemporaryTimeTableUpdate):
    db_temp = db.query(TemporaryTimeTable).filter(TemporaryTimeTable.id == temp_id).first()
    if not db_temp:
        return None

    temp_dict = temp_data.dict(exclude_unset=True)

    if "academic_period_id" in temp_dict:
        academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.id == temp_dict["academic_period_id"]).first()
        if not academic_period:
            raise HTTPException(status_code=404, detail="Academic period tidak ditemukan")

    for key, value in temp_dict.items():
        setattr(db_temp, key, value)

    db.commit()
    db.refresh(db_temp)
    return db_temp

def delete_temporary_timetable(db: Session, temp_id: int):
    db_temp = db.query(TemporaryTimeTable).filter(TemporaryTimeTable.id == temp_id).first()
    if not db_temp:
        return None
    db.delete(db_temp)
    db.commit()
    return db_temp

# ====== ROUTERS ======
@router.post("/", response_model=TemporaryTimeTableResponse)
def create_temporary_timetable_endpoint(temp: TemporaryTimeTableCreate, db: Session = Depends(get_db)):
  
    existing_temp = (
        db.query(TemporaryTimeTable)
        .filter(TemporaryTimeTable.timetable_id == temp.timetable_id)
        .filter(TemporaryTimeTable.end_date >= datetime.now())  
        .first()
    )

    if existing_temp:
        raise HTTPException(
            status_code=400,
            detail=f"Kelas Pengganti dengan ID tersebut sudah ada"
        )

    return create_temporary_timetable(db, temp)


@router.get("/", response_model=List[TemporaryTimeTableResponse])
def get_all_temporary_timetables_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_temporary_timetables(db, skip, limit)


@router.get("/mahasiswa/{mahasiswa_id}", response_model=Dict[str, Any])
async def get_temporary_timetable_by_mahasiswa(
    mahasiswa_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):

    
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=404, detail=" active academic period tidak ditemukan")

    try:
      
        query = db.query(
            TemporaryTimeTable.id,
            TemporaryTimeTable.timetable_id,
            TemporaryTimeTable.new_ruangan_id,
            TemporaryTimeTable.new_timeslot_ids,
            TemporaryTimeTable.start_date,
            TemporaryTimeTable.end_date,
            TimeTable.kelas,
            TemporaryTimeTable.change_reason,
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
            ).label("dosen_names")
        ).join(TimeTable, TemporaryTimeTable.timetable_id == TimeTable.id) \
         .join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk) \
         .join(Ruangan, TemporaryTimeTable.new_ruangan_id == Ruangan.id) \
         .join(Dosen, OpenedClass.dosens) \
         .join(MahasiswaTimeTable, MahasiswaTimeTable.timetable_id == TimeTable.id) \
         .filter(
             and_(
                 MahasiswaTimeTable.mahasiswa_id == mahasiswa_id,
                 TimeTable.academic_period_id == active_period.id,
                #  TemporaryTimeTable.start_date <= datetime.now(),
                #  TemporaryTimeTable.end_date >= datetime.now()
             )
         ) \
         .group_by(
             TemporaryTimeTable.id,
             TimeTable.id,
             OpenedClass.id,
             MataKuliah.kodemk,
             MataKuliah.namamk,
             MataKuliah.kurikulum,
             MataKuliah.sks,
             MataKuliah.smt,
             Ruangan.nama_ruang
         )

        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )

  
        total_records = query.count()
        total_pages = (total_records + page_size - 1) // page_size

        temporary_data = query.offset((page - 1) * page_size).limit(page_size).all()

        timeslot_ids = set(
            ts_id for entry in temporary_data for ts_id in entry.new_timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        formatted_timetable = []
        for entry in temporary_data:
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
                for ts_id in entry.new_timeslot_ids if (ts := timeslot_map.get(ts_id))
            ]

            if formatted_timeslots:
                sorted_slots = sorted(formatted_timeslots, key=lambda x: x["start_time"])
                day = sorted_slots[0]["day"]
                schedule = f"{day}\t{sorted_slots[0]['start_time']} - {sorted_slots[-1]['end_time']}"
            else:
                schedule = "-"

            formatted_entry = {
                "temporary_timetable_id": entry.id,
                "timetable_id": entry.timetable_id,
                "kodemk": entry.kodemk,
                "matakuliah": entry.namamk,
                "kurikulum": entry.kurikulum,
                "kelas": entry.kelas,
                "kap_peserta": "-",  
                "sks": entry.sks,
                "smt": entry.smt,
                "dosen": formatted_dosen,
                "ruangan": entry.ruangan_name,
                "schedule": schedule,
                "start_date": entry.start_date.strftime("%Y-%m-%d"),
                "end_date": entry.end_date.strftime("%Y-%m-%d"),
                "change_reason": entry.change_reason or "-"
            }

            formatted_timetable.append(formatted_entry)

        return {
            "mahasiswa_id": mahasiswa_id,
            "academic_period": {
                "id": active_period.id,
                "tahun_ajaran": active_period.tahun_ajaran,
                "semester": active_period.semester,
                "start_date": active_period.start_date,
                "end_date": active_period.end_date,
                "is_active": active_period.is_active,
            },
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": formatted_timetable,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dosen/{dosen_id}", response_model=Dict[str, Any])
async def get_temporary_timetable_by_dosen(
    dosen_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
   

    dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
    if not dosen:
        raise HTTPException(status_code=404, detail="Dosen not found")

    try:
        query = db.query(
            TemporaryTimeTable.id,
            TemporaryTimeTable.timetable_id,
            TemporaryTimeTable.new_ruangan_id,
            TemporaryTimeTable.new_timeslot_ids,
            TemporaryTimeTable.start_date,
            TemporaryTimeTable.end_date,
            TimeTable.kelas,
            TemporaryTimeTable.change_reason,
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
            ).label("dosen_names")
        ).join(TimeTable, TemporaryTimeTable.timetable_id == TimeTable.id) \
         .join(AcademicPeriods, TimeTable.academic_period_id == AcademicPeriods.id) \
         .join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk) \
         .join(Ruangan, TemporaryTimeTable.new_ruangan_id == Ruangan.id) \
         .join(Dosen, OpenedClass.dosens) \
         .join(User, Dosen.user_id == User.id) \
         .filter(
             and_(
                 OpenedClass.dosens.any(Dosen.pegawai_id == dosen_id),
                 AcademicPeriods.is_active == True  
             )
         ) \
         .group_by(
             TemporaryTimeTable.id,
             TimeTable.id,
            
             OpenedClass.id,
             MataKuliah.kodemk,
             MataKuliah.namamk,
             MataKuliah.kurikulum,
             
             MataKuliah.sks,
             MataKuliah.smt,
             Ruangan.nama_ruang
         )

        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )

       
        total_records = query.count()
        total_pages = (total_records + page_size - 1) // page_size

        temporary_data = query.offset((page - 1) * page_size).limit(page_size).all()

        timeslot_ids = set(
            ts_id for entry in temporary_data for ts_id in entry.new_timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        formatted_timetable = []
        for entry in temporary_data:
           
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
                for ts_id in entry.new_timeslot_ids if (ts := timeslot_map.get(ts_id))
            ]

           
            if formatted_timeslots:
                sorted_slots = sorted(formatted_timeslots, key=lambda x: x["start_time"])
                day = sorted_slots[0]["day"]
                schedule = f"{day}\t{sorted_slots[0]['start_time']} - {sorted_slots[-1]['end_time']}"
            else:
                schedule = "-"

            formatted_entry = {
                "temporary_timetable_id": entry.id,
                "timetable_id": entry.timetable_id,
                "kodemk": entry.kodemk,
                "matakuliah": entry.namamk,
                "kurikulum": entry.kurikulum,
                "kelas": entry.kelas, 
                "kap_peserta": "-",  
                "sks": entry.sks,
                "smt": entry.smt,
                "dosen": formatted_dosen,
                "ruangan": entry.ruangan_name,
                "schedule": schedule,
                "start_date": entry.start_date.strftime("%Y-%m-%d"),
                "end_date": entry.end_date.strftime("%Y-%m-%d"),
                "change_reason": entry.change_reason or "-"
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

@router.get("/{temp_id}", response_model=TemporaryTimeTableResponse)
def get_temporary_timetable_endpoint(temp_id: int, db: Session = Depends(get_db)):
    db_temp = get_temporary_timetable_by_id(db, temp_id)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable tidak ditemukan")
    return db_temp

@router.put("/{temp_id}", response_model=TemporaryTimeTableResponse)
def update_temporary_timetable_endpoint(temp_id: int, temp: TemporaryTimeTableUpdate, db: Session = Depends(get_db)):
    db_temp = update_temporary_timetable(db, temp_id, temp)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable tidak ditemukan")
    return db_temp


@router.delete("/{temp_id}")
def delete_temporary_timetable_endpoint(temp_id: int, db: Session = Depends(get_db)):
    db_temp = delete_temporary_timetable(db, temp_id)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable tidak ditemukan")
    return {"detail": "Temporary timetable berhasil dihapus"}
