import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
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
    is_conflicted: bool
    kelas: str
    kapasitas: int
    reason: Optional[str] = None
    academic_period_id: int
    kuota: int
    placeholder: Optional[str] = None

class TimeTableCreate(TimeTableBase):
    pass

class TimeTableUpdate(TimeTableBase):
    pass

class TimeTableResponse(TimeTableBase):
    id: int

    class Config:
        orm_mode = True



# 🟢 CREATE a new TimeTable entry
@router.post("/", response_model=TimeTableResponse)
def create_timetable(timetable: TimeTableCreate, db: Session = Depends(get_db)):
    new_timetable = TimeTable(
        opened_class_id=timetable.opened_class_id,
        ruangan_id=timetable.ruangan_id,
        timeslot_ids=timetable.timeslot_ids,
        is_conflicted=timetable.is_conflicted,
        kelas=timetable.kelas,
        kapasitas=timetable.kapasitas,
        reason=timetable.reason,
        academic_period_id=timetable.academic_period_id,
        kuota=timetable.kuota,
        placeholder=timetable.placeholder,
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
        print(f"🔍 Found TimeSlot IDs for {day}: {timeslot_ids}")  # Debugging Output

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
@router.get("/{id}", response_model=TimeTableResponse)
def get_timetable(id: int, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return timetable


# 🟠 UPDATE a timetable by ID
@router.put("/{id}", response_model=TimeTableResponse)
def update_timetable(id: int, updated_timetable: TimeTableUpdate, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    for key, value in updated_timetable.dict(exclude_unset=True).items():
        setattr(timetable, key, value)

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


