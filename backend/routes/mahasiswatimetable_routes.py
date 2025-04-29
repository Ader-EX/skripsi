from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from model.academicperiod_model import AcademicPeriods
from model.user_model import User
from model.dosen_model import Dosen
from model.timeslot_model import TimeSlot
from model.openedclass_model import OpenedClass
from model.matakuliah_model import MataKuliah
from model.mahasiswatimetable_model import MahasiswaTimeTable
from model.mahasiswa_model import Mahasiswa
from model.timetable_model import TimeTable
from database import get_db
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

router = APIRouter()


class MahasiswaTimeTableBase(BaseModel):
    mahasiswa_id: int
    timetable_id: int
    academic_period_id: int

class MahasiswaTimeTableCreate(MahasiswaTimeTableBase):
    pass

class MahasiswaTimeTableRead(MahasiswaTimeTableBase):
    id: int

    class Config:
        orm_mode = True


@router.post("/", response_model=MahasiswaTimeTableRead, status_code=status.HTTP_201_CREATED)
async def add_lecture_to_timetable(entry: MahasiswaTimeTableCreate, db: Session = Depends(get_db)):
  
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == entry.mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    timetable = db.query(TimeTable).filter(TimeTable.id == entry.timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable tidak ditemukan")

    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=400, detail=" active academic period tidak ditemukan")

    if timetable.kuota >= timetable.kapasitas:
        raise HTTPException(status_code=400, detail="Kelas sudah penuh")

    opened_class = db.query(OpenedClass).filter(OpenedClass.id == timetable.opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened Class tidak ditemukan")

    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == opened_class.mata_kuliah_kodemk).first()
    if not mata_kuliah:
        raise HTTPException(status_code=404, detail="Mata Kuliah tidak ditemukan")

    selected_class = opened_class.kelas  

    existing_kodemk_entry = db.query(MahasiswaTimeTable).join(TimeTable).join(OpenedClass).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        OpenedClass.mata_kuliah_kodemk == mata_kuliah.kodemk,
        OpenedClass.kelas != selected_class  
    ).first()

    if existing_kodemk_entry:
        raise HTTPException(
            status_code=400, 
            detail=f"Sudah masuk ke {mata_kuliah.kodemk} dengan kelas yang berbeda ({existing_kodemk_entry.timetable.opened_class.kelas})"
        )

    # biar mahasiswa tidak bisa mengambil mata kuliah yang berhubungan dengan kelas yang berbeda
    related_courses = db.query(MahasiswaTimeTable).join(TimeTable).join(OpenedClass).join(MataKuliah).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MataKuliah.namamk.ilike(f"%{mata_kuliah.namamk.replace('Praktikum', '').strip()}%"),
        OpenedClass.kelas != selected_class 
    ).first()

    if related_courses:
        raise HTTPException(
            status_code=400, 
            detail=f"Tidak bisa mengambil {mata_kuliah.namamk} di kelas {selected_class} karena user telah mengambil kelas yang sama tapi beda kelas ({related_courses.timetable.opened_class.kelas})"
        )

    existing_entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MahasiswaTimeTable.timetable_id == entry.timetable_id
    ).first()

    if existing_entry:
        raise HTTPException(status_code=400, detail="Timetable sudab ditambahkan ke mahasiswa schedule")

    mahasiswa.sks_diambil += mata_kuliah.sks  
    db.commit()  

    new_entry = MahasiswaTimeTable(
        mahasiswa_id=entry.mahasiswa_id,
        timetable_id=entry.timetable_id,
        academic_period_id=active_period.id  
    )
    db.add(new_entry)

    timetable.kuota += 1  
    db.commit()
    db.refresh(new_entry)

    return new_entry


@router.get("/{mahasiswa_id}", response_model=List[MahasiswaTimeTableRead])
async def get_timetable_by_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    timetable_entries = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id).all()

    if not timetable_entries:
        raise HTTPException(status_code=404, detail="No timetable entries ditemukan untuk mahasiswa ini")

    return timetable_entries


@router.get("/timetable/{mahasiswa_id}", response_model=Dict[str, Any])
async def get_timetable_by_mahasiswa(
    mahasiswa_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk")
):
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=404, detail="No active academic period found")

    try:
        query = db.query(
            TimeTable.id,
            TimeTable.opened_class_id,
            TimeTable.ruangan_id,
            TimeTable.timeslot_ids,
            TimeTable.placeholder,
            TimeTable.kelas,
            TimeTable.kapasitas,
            TimeTable.kuota,
            OpenedClass.mata_kuliah_kodemk,
            MataKuliah.kodemk,
            MataKuliah.namamk,
            MataKuliah.sks,
            MataKuliah.smt,
            MataKuliah.kurikulum,
            MataKuliah.sks,
            MataKuliah.smt,
            func.group_concat(
                func.concat_ws(" ", Dosen.title_depan, Dosen.nama, Dosen.title_belakang)
                .distinct()
                .op('SEPARATOR')('||')
            ).label("dosen_names")  
        ).join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk) \
         .join(Dosen, OpenedClass.dosens) \
         .join(User, Dosen.user_id == User.id) \
         .join(MahasiswaTimeTable, MahasiswaTimeTable.timetable_id == TimeTable.id) \
         .filter(
            MahasiswaTimeTable.mahasiswa_id == mahasiswa_id,
            TimeTable.academic_period_id == active_period.id  
         ) \
         .group_by(
            TimeTable.id, OpenedClass.id, MataKuliah.kodemk, MataKuliah.namamk, 
            MataKuliah.kurikulum, MataKuliah.sks, MataKuliah.smt
         )

        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )

        timetable_data = query.all()

        timeslot_ids = set(
            ts_id for entry in timetable_data for ts_id in entry.timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        formatted_timetable = []
        for entry in timetable_data:
            formatted_dosen = (
                "\n".join([f"{i+1}. {dosen.strip()}" for i, dosen in enumerate(entry.dosen_names.split("||"))])
                if entry.dosen_names else "-"
            )

            formatted_timeslots = [
                {
                    "id": ts.id,
                    "day": ts.day,
                    "start_time": ts.start_time.strftime("%H:%M"),
                    "end_time": ts.end_time.strftime("%H:%M"),
                }
                for ts_id in entry.timeslot_ids if (ts := timeslot_map.get(ts_id))
            ]

            formatted_entry = {
                "timetable_id": entry.id,
                "kodemk": entry.kodemk,
                "matakuliah": entry.namamk,
                "kurikulum": entry.kurikulum,
                "kelas": entry.kelas,
                "kap_peserta": f"{entry.kapasitas} / {entry.kuota}",
                "sks": entry.sks,
                "smt": entry.smt,
                "dosen": formatted_dosen,
                "timeslots": formatted_timeslots,
                "placeholder": entry.placeholder,
            }
            formatted_timetable.append(formatted_entry)

        return {
            "mahasiswa_id": mahasiswa_id,
            "academic_period": {
                "id": active_period.id,
                "tahun_ajaran": active_period.tahun_ajaran,
                "semester": active_period.semester,
                "week_start": active_period.start_date,
                "week_end": active_period.end_date,
                "is_active": active_period.is_active,
            },
            "data": formatted_timetable,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/timetable/{mahasiswa_id}/{timetable_id}", status_code=status.HTTP_200_OK)
async def delete_timetable_entry(mahasiswa_id: int, timetable_id: int, db: Session = Depends(get_db)):
 
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa tidak ditemukan")

    timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable entry tidak ditemukan")

    entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == mahasiswa_id,
        MahasiswaTimeTable.timetable_id == timetable_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry tidak ditemukan for this mahasiswa")

    db.delete(entry)

    mata_kuliah = (
        db.query(MataKuliah)
        .join(OpenedClass, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk)
        .join(TimeTable, TimeTable.opened_class_id == OpenedClass.id)
        .filter(TimeTable.id == timetable_id)
        .first()
    )

    if mata_kuliah:
        mahasiswa.sks_diambil -= mata_kuliah.sks  
        if mahasiswa.sks_diambil < 0:
            mahasiswa.sks_diambil = 0  

    if timetable.kuota > 0:
        timetable.kuota -= 1  

    db.commit()  

    return {"message": "Timetable entry berhasil dihapus, kuota updated"}
