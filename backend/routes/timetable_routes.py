from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from model.timetable_model import TimeTable
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# Pydantic Models
class TimeTableBase(BaseModel):
    pengajaran_id: int
    ruangan_id: int
    timeslot_id: int
    kelas: str
    kapasitas: Optional[int] = 35
    reason: Optional[str] = None
    academic_period_id: int
    sks: Optional[int] = 1

class TimeTableCreate(TimeTableBase):
    pass

class TimeTableRead(TimeTableBase):
    id: int
    is_conflicted: bool

    class Config:
        orm_mode = True

class TimeTableUpdate(BaseModel):
    kapasitas: Optional[int] = None
    reason: Optional[str] = None
    is_conflicted: Optional[bool] = None

# Routes
@router.post("/timetables", response_model=TimeTableRead, status_code=status.HTTP_201_CREATED)
async def create_timetable(timetable: TimeTableCreate, db: Session = Depends(get_db)):
    # Ensure there is no conflict with the timeslot and room for the same academic period
    existing_timetable = db.query(TimeTable).filter(
        TimeTable.ruangan_id == timetable.ruangan_id,
        TimeTable.timeslot_id == timetable.timeslot_id,
        TimeTable.academic_period_id == timetable.academic_period_id
    ).first()

    if existing_timetable:
        raise HTTPException(status_code=400, detail="Conflicting timetable already exists")

    new_timetable = TimeTable(**timetable.dict())
    db.add(new_timetable)
    db.commit()
    db.refresh(new_timetable)
    return new_timetable

@router.get("/timetables/{timetable_id}", response_model=TimeTableRead)
async def get_timetable(timetable_id: int, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="TimeTable not found")
    return timetable

@router.get("/timetables", response_model=List[TimeTableRead])
async def get_all_timetables(
    academic_period_id: Optional[int] = Query(None, description="Filter by academic period"),
    kelas: Optional[str] = Query(None, description="Filter by class"),
    db: Session = Depends(get_db)
):
    query = db.query(TimeTable)
    if academic_period_id:
        query = query.filter(TimeTable.academic_period_id == academic_period_id)
    if kelas:
        query = query.filter(TimeTable.kelas == kelas)
    return query.all()

@router.put("/timetables/{timetable_id}", response_model=TimeTableRead)
async def update_timetable(timetable_id: int, updated_data: TimeTableUpdate, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="TimeTable not found")

    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(timetable, key, value)

    db.commit()
    db.refresh(timetable)
    return timetable

@router.delete("/timetables/{timetable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable(timetable_id: int, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="TimeTable not found")

    db.delete(timetable)
    db.commit()
    return {"message": "TimeTable deleted successfully"}
