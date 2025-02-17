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

# 🔹 **Pydantic Models**
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


# ✅ **POST: Add Mahasiswa to Timetable**
@router.post("/", response_model=MahasiswaTimeTableRead, status_code=status.HTTP_201_CREATED)
async def add_lecture_to_timetable(entry: MahasiswaTimeTableCreate, db: Session = Depends(get_db)):
    # Check if Mahasiswa exists
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == entry.mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # Check if Timetable exists
    timetable = db.query(TimeTable).filter(TimeTable.id == entry.timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Get Active Academic Period
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=400, detail="No active academic period found")

    # Check if the class is full
    if timetable.kuota >= timetable.kapasitas:
        raise HTTPException(status_code=400, detail="Class is full, cannot add more students")

    # Get the OpenedClass associated with the timetable
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == timetable.opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened Class not found")

    # Get MataKuliah directly from OpenedClass
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == opened_class.mata_kuliah_kodemk).first()
    if not mata_kuliah:
        raise HTTPException(status_code=404, detail="Mata Kuliah not found")

    # Get the class (e.g., "A", "B", etc.)
    selected_class = opened_class.kelas  

    # Prevent selecting the same kodemk with different classes
    existing_kodemk_entry = db.query(MahasiswaTimeTable).join(TimeTable).join(OpenedClass).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        OpenedClass.mata_kuliah_kodemk == mata_kuliah.kodemk,
        OpenedClass.kelas != selected_class  # Prevent different classes
    ).first()

    if existing_kodemk_entry:
        raise HTTPException(
            status_code=400, 
            detail=f"Already enrolled in {mata_kuliah.kodemk} with a different class ({existing_kodemk_entry.timetable.opened_class.kelas})"
        )

    # Prevent students from taking related courses with different classes
    related_courses = db.query(MahasiswaTimeTable).join(TimeTable).join(OpenedClass).join(MataKuliah).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MataKuliah.namamk.ilike(f"%{mata_kuliah.namamk.replace('Praktikum', '').strip()}%"),
        OpenedClass.kelas != selected_class  # Ensure same class
    ).first()

    if related_courses:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot take {mata_kuliah.namamk} in class {selected_class} because you have taken a related course in a different class ({related_courses.timetable.opened_class.kelas})"
        )

    # Check for duplicate entries
    existing_entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MahasiswaTimeTable.timetable_id == entry.timetable_id
    ).first()

    if existing_entry:
        raise HTTPException(status_code=400, detail="Timetable already added to the mahasiswa's schedule")

    # Update Mahasiswa's `sks_diambil`
    mahasiswa.sks_diambil += mata_kuliah.sks  # Add SKS from MataKuliah
    db.commit()  # Commit update to Mahasiswa

    # Create a new MahasiswaTimeTable entry
    new_entry = MahasiswaTimeTable(
        mahasiswa_id=entry.mahasiswa_id,
        timetable_id=entry.timetable_id,
        academic_period_id=active_period.id  # ✅ Assign the active academic period
    )
    db.add(new_entry)

    # **Increment `kuota` after successfully adding the student**
    timetable.kuota += 1  
    db.commit()  # Commit both the new entry and the updated `kuota`
    db.refresh(new_entry)

    return new_entry


# ✅ **GET: Get Mahasiswa's Timetable**
@router.get("/{mahasiswa_id}", response_model=List[MahasiswaTimeTableRead])
async def get_timetable_by_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    timetable_entries = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id).all()

    if not timetable_entries:
        raise HTTPException(status_code=404, detail="No timetable entries found for this mahasiswa")

    return timetable_entries


@router.get("/timetable/{mahasiswa_id}", response_model=Dict[str, Any])
async def get_timetable_by_mahasiswa(
    mahasiswa_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk")
):
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # ✅ Fetch the active academic period
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=404, detail="No active academic period found")

    try:
        # ✅ Fetch timetable data within the active academic period
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
            TimeTable.academic_period_id == active_period.id  # ✅ Ensure only active academic period data
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

        # ✅ Fetch timeslot details in a single query
        timeslot_ids = set(
            ts_id for entry in timetable_data for ts_id in entry.timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        formatted_timetable = []
        for entry in timetable_data:
            # ✅ Format Dosen names into a numbered list
            formatted_dosen = (
                "\n".join([f"{i+1}. {dosen.strip()}" for i, dosen in enumerate(entry.dosen_names.split("||"))])
                if entry.dosen_names else "-"
            )

            # ✅ Fetch timeslot details
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
                "semester": active_period.semester
            },
            "data": formatted_timetable,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/timetable/{mahasiswa_id}/{timetable_id}", status_code=status.HTTP_200_OK)
async def delete_timetable_entry(mahasiswa_id: int, timetable_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific timetable entry for a mahasiswa and updates the `kuota` count.
    """
    # Check if Mahasiswa exists
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    # Check if Timetable exists
    timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    # Check if Mahasiswa is enrolled in this timetable
    entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == mahasiswa_id,
        MahasiswaTimeTable.timetable_id == timetable_id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found for this mahasiswa")

    # ✅ Remove the timetable entry
    db.delete(entry)

    # ✅ Update mahasiswa's total SKS
    mata_kuliah = (
        db.query(MataKuliah)
        .join(OpenedClass, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk)
        .join(TimeTable, TimeTable.opened_class_id == OpenedClass.id)
        .filter(TimeTable.id == timetable_id)
        .first()
    )

    if mata_kuliah:
        mahasiswa.sks_diambil -= mata_kuliah.sks  # Deduct SKS
        if mahasiswa.sks_diambil < 0:
            mahasiswa.sks_diambil = 0  # Prevent negative SKS

    # ✅ Decrement `kuota` in `TimeTable`
    if timetable.kuota > 0:
        timetable.kuota -= 1  # Reduce enrolled students count

    db.commit()  # Commit all changes

    return {"message": "Timetable entry deleted successfully, kuota updated"}
