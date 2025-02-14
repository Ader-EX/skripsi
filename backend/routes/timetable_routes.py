import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from model.ruangan_model import Ruangan
from model.academicperiod_model import AcademicPeriods
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from database import get_db
from model.timetable_model import TimeTable
from model.timeslot_model import TimeSlot
from typing import List




router = APIRouter()


from pydantic import BaseModel
from typing import List, Optional

class TimeTableBase(BaseModel):
    opened_class_id: int
    ruangan_id: int
    timeslot_ids: List[int]
    is_conflicted: bool = False
    kelas: str
    kapasitas: int
    reason: Optional[str] = None
    academic_period_id: int
    kuota: int = 0
    placeholder: Optional[str] = None





class TimeTableUpdate(TimeTableBase):
    opened_class_id: Optional[int] = None
    ruangan_id: Optional[int] = None
    timeslot_ids: Optional[List[int]] = None
    is_conflicted: Optional[bool] = False
    kelas: Optional[str] = None
    kapasitas: Optional[int] = None
    reason: Optional[str] = None
    academic_period_id: Optional[int] = None
    kuota: Optional[int] = 0
    placeholder: Optional[str] = None


class TimeTableCreate(TimeTableUpdate):
    pass
class TimeTableResponse(TimeTableBase):
    id: int

    class Config:
        orm_mode = True



from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from model.timetable_model import TimeTable
from model.openedclass_model import OpenedClass
from model.matakuliah_model import MataKuliah
from model.academicperiod_model import AcademicPeriods
from model.timeslot_model import TimeSlot
from database import get_db
import json

@router.post("/", response_model=TimeTableResponse)
def create_timetable(timetable: TimeTableCreate, db: Session = Depends(get_db)):
    # 1️⃣ Check if `opened_class_id` already exists
    existing_class = db.query(TimeTable).filter(TimeTable.opened_class_id == timetable.opened_class_id).first()
    if existing_class:
        raise HTTPException(status_code=400, detail="This opened class already has a timetable entry.")

    # 2️⃣ Prevent room conflict in `ruangan_id`
    for timeslot in timetable.timeslot_ids:
        conflict = db.query(TimeTable).filter(
            TimeTable.ruangan_id == timetable.ruangan_id,
            func.json_contains(TimeTable.timeslot_ids, json.dumps([timeslot]))
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Room {timetable.ruangan_id} is already booked for timeslot {timeslot}.")

    # 3️⃣ Fetch the active `academic_period_id`
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=404, detail="No active academic period found.")

    academic_period_id = active_period.id

    # 4️⃣ Get `kapasitas` and `kelas` from `OpenedClass`
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == timetable.opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class not found.")

    kapasitas = opened_class.kapasitas
    kelas = opened_class.kelas  # Ensure this value is retrieved correctly

    # 5️⃣ Fetch Timeslot Details to Generate Placeholder
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timetable.timeslot_ids)).all()
    if timeslots:
        timeslot_str = f"{timetable.ruangan_id} - {timeslots[0].day} ({timeslots[0].start_time} - {timeslots[-1].end_time})"
    else:
        timeslot_str = f"{timetable.ruangan_id} - Unknown TimeSlot"

    selected_class_times = [f"1. {timeslot_str}"]

    # 6️⃣ Find `kelas A` for the same `mata_kuliah_kodemk`
    mata_kuliah_kodemk = opened_class.mata_kuliah_kodemk
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == mata_kuliah_kodemk).first()

    kelas_a = db.query(OpenedClass).filter(
        OpenedClass.mata_kuliah_kodemk == mata_kuliah_kodemk,
        OpenedClass.kelas == "A"
    ).first()

    if kelas_a:
        kelas_a_timetable = db.query(TimeTable).filter(TimeTable.opened_class_id == kelas_a.id).first()
        if kelas_a_timetable:
            kelas_a_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(kelas_a_timetable.timeslot_ids)).all()
            if kelas_a_timeslots:
                kelas_a_str = f"{kelas_a_timetable.ruangan_id} - {kelas_a_timeslots[0].day} ({kelas_a_timeslots[0].start_time} - {kelas_a_timeslots[-1].end_time})"
                if mata_kuliah and mata_kuliah.tipe_mk == "T":
                    selected_class_times.append(f"2. {kelas_a_str}")

    # 7️⃣ Generate final placeholder string
    placeholder = "\n".join(selected_class_times)

    # ✅ Create new timetable entry
    new_timetable = TimeTable(
        opened_class_id=timetable.opened_class_id,
        ruangan_id=timetable.ruangan_id,
        timeslot_ids=timetable.timeslot_ids,
        is_conflicted=False,  # Always False
        kelas=kelas,  # Ensure this value is included
        kapasitas=kapasitas,  # Ensure this value is included
        reason=None,
        academic_period_id=academic_period_id,  # Ensure active period is assigned
        kuota=0,  # Always 0 for POST
        placeholder=placeholder,
    )

    db.add(new_timetable)
    db.commit()
    db.refresh(new_timetable)
    return new_timetable



# 🔵 READ all timetables
@router.get("/", response_model=List[TimeTableResponse])
def get_all_timetables(db: Session = Depends(get_db)):
    return db.query(TimeTable).all()




@router.get("/filter", response_model=List[TimeTableResponse])
def get_timetable_by_day_and_room(
    day: Optional[str] = None, room_id: Optional[int] = None, db: Session = Depends(get_db)
):
    query = db.query(TimeTable)

    if day:
        timeslot_ids = [t.id for t in db.query(TimeSlot).filter(TimeSlot.day == day).all()]
        if timeslot_ids:
            timeslot_json = json.dumps(timeslot_ids)
            query = query.filter(func.json_contains(TimeTable.timeslot_ids, timeslot_json))
        else:
            raise HTTPException(status_code=404, detail=f"No timeslots found for {day}")

    if room_id:
        query = query.filter(TimeTable.ruangan_id == room_id)

    timetables = query.all()
    if not timetables:
        raise HTTPException(status_code=404, detail="No timetables found with the given filters")

    return timetables



# 🔵 READ a single timetable by ID
@router.get("/{id}")
def get_timetable(id: int, db: Session = Depends(get_db)):
    timetable = (
        db.query(TimeTable)
        .filter(TimeTable.id == id)
        .join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id)
        .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk)
        .join(Ruangan, TimeTable.ruangan_id == Ruangan.id)
        .add_columns(
            MataKuliah.namamk.label("mata_kuliah_nama"),
            Ruangan.nama_ruang.label("ruangan_nama")
        )
        .first()
    )

    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    timetable_data = {
        "id": timetable.TimeTable.id,
        "opened_class_id": timetable.TimeTable.opened_class_id,
        "ruangan_id": timetable.TimeTable.ruangan_id,
        "timeslot_ids": timetable.TimeTable.timeslot_ids,
        "is_conflicted": timetable.TimeTable.is_conflicted,
        "kelas": timetable.TimeTable.kelas,
        "kapasitas": timetable.TimeTable.kapasitas,
        "reason": timetable.TimeTable.reason,
        "academic_period_id": timetable.TimeTable.academic_period_id,
        "kuota": timetable.TimeTable.kuota,
        "placeholder": timetable.TimeTable.placeholder,
        "mata_kuliah_nama": timetable.mata_kuliah_nama,
        "ruangan_nama": timetable.ruangan_nama
    }

    return timetable_data


@router.put("/{id}", response_model=TimeTableResponse)
def update_timetable(id: int, updated_timetable: TimeTableUpdate, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found.")

    # Prevent updating to another `opened_class_id` if it already exists
    if updated_timetable.opened_class_id and updated_timetable.opened_class_id != timetable.opened_class_id:
        existing_class = db.query(TimeTable).filter(TimeTable.opened_class_id == updated_timetable.opened_class_id).first()
        if existing_class:
            raise HTTPException(status_code=400, detail="This opened class already has a timetable entry.")

    # Prevent room conflict in `ruangan_id`
    if updated_timetable.ruangan_id:
        for timeslot in updated_timetable.timeslot_ids or timetable.timeslot_ids:
            conflict = db.query(TimeTable).filter(
                TimeTable.ruangan_id == updated_timetable.ruangan_id,
                func.json_contains(TimeTable.timeslot_ids, json.dumps([timeslot])),
                TimeTable.id != id  # Exclude itself from the conflict check
            ).first()
            if conflict:
                raise HTTPException(status_code=400, detail=f"Room {updated_timetable.ruangan_id} is already booked for timeslot {timeslot}.")

    # ✅ Fetch Timeslot Details
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(updated_timetable.timeslot_ids or timetable.timeslot_ids)).all()
    
    # ✅ Generate Correct Placeholder Entry for Current Class
    if timeslots:
        timeslot_str = f"{updated_timetable.ruangan_id} - {timeslots[0].day} ({timeslots[0].start_time} - {timeslots[-1].end_time})"
    else:
        timeslot_str = f"{updated_timetable.ruangan_id} - Unknown TimeSlot"

    selected_class_times = [f"1. {timeslot_str}"]

    # ✅ Find `kelas A` for the same `mata_kuliah_kodemk`
    mata_kuliah_kodemk = timetable.opened_class.mata_kuliah_kodemk
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == mata_kuliah_kodemk).first()

    kelas_a = db.query(OpenedClass).filter(
        OpenedClass.mata_kuliah_kodemk == mata_kuliah_kodemk,
        OpenedClass.kelas == "A"
    ).first()

    if kelas_a:
        kelas_a_timetable = db.query(TimeTable).filter(TimeTable.opened_class_id == kelas_a.id).first()
        if kelas_a_timetable:
            kelas_a_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(kelas_a_timetable.timeslot_ids)).all()
            if kelas_a_timeslots:
                kelas_a_str = f"{kelas_a_timetable.ruangan_id} - {kelas_a_timeslots[0].day} ({kelas_a_timeslots[0].start_time} - {kelas_a_timeslots[-1].end_time})"
                if mata_kuliah and mata_kuliah.tipe_mk == "T":
                    selected_class_times.append(f"2. {kelas_a_str}")

    # ✅ Generate final placeholder string
    updated_placeholder = "\n".join(selected_class_times)

    # ✅ Merge updated fields
    for key, value in updated_timetable.dict(exclude_unset=True).items():
        setattr(timetable, key, value)

    timetable.placeholder = updated_placeholder  # Overwrite placeholder
    db.commit()
    db.refresh(timetable)
    return timetable






# 🔴 DELETE a timetable by ID
@router.delete("/{id}")
def delete_timetable(id: int, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    db.delete(timetable)
    db.commit()
    return {"message": "Timetable deleted successfully"}


