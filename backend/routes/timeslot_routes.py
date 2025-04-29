from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import time
from database import get_db
from model.timeslot_model import TimeSlot
from pydantic import BaseModel, Field

router = APIRouter()

# Pydantic Models
class TimeSlotBase(BaseModel):
    day: str = Field(..., example="Monday", description="The day of the week")
    start_time: time = Field(..., example="07:00", description="Start time in HH:MM format")
    end_time: time = Field(..., example="07:50", description="End time in HH:MM format")
    day_index: int = Field(..., example="1", description="Day index (0=Monday, 1=Tuesday, etc.)")

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotRead(TimeSlotBase):
    id: int

    class Config:
        orm_mode = True


@router.post("/", response_model=TimeSlotRead, status_code=status.HTTP_201_CREATED)
async def create_timeslot(timeslot: TimeSlotCreate, db: Session = Depends(get_db)):
    
    conflict = db.query(TimeSlot).filter(
        TimeSlot.day == timeslot.day,
        TimeSlot.start_time < timeslot.end_time,
        TimeSlot.end_time > timeslot.start_time
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="TimeSlot bertabrakan dengan yang sudah ada")

    # Create the timeslot
    new_timeslot = TimeSlot(**timeslot.dict())
    db.add(new_timeslot)
    db.commit()
    db.refresh(new_timeslot)
    return new_timeslot


# Read TimeSlot by ID
@router.get("/{timeslot_id}", response_model=TimeSlotRead)
async def read_timeslot(timeslot_id: int, db: Session = Depends(get_db)):
    timeslot = db.query(TimeSlot).filter(TimeSlot.id == timeslot_id).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="TimeSlot tidak ditemukan")
    return timeslot


# Read All TimeSlots
@router.get("/", response_model=List[TimeSlotRead])
async def read_all_timeslots(
    day: Optional[str] = Query(None, description="Filter timeslots berdasarkan hari"),
    db: Session = Depends(get_db),
):
    query = db.query(TimeSlot)
    if day:
        query = query.filter(TimeSlot.day == day)
    return query.all()


# Update TimeSlot
@router.put("/{timeslot_id}", response_model=TimeSlotRead)
async def update_timeslot(timeslot_id: int, updated_timeslot: TimeSlotCreate, db: Session = Depends(get_db)):
    timeslot = db.query(TimeSlot).filter(TimeSlot.id == timeslot_id).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="TimeSlot tidak ditemukan")

    conflict = db.query(TimeSlot).filter(
        TimeSlot.day == updated_timeslot.day,
        TimeSlot.start_time < updated_timeslot.end_time,
        TimeSlot.end_time > updated_timeslot.start_time,
        TimeSlot.id != timeslot_id
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Updated TimeSlot bertabrakan dengan yang sudah ada")

    for key, value in updated_timeslot.dict().items():
        setattr(timeslot, key, value)

    db.commit()
    db.refresh(timeslot)
    return timeslot


@router.delete("/{timeslot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeslot(timeslot_id: int, db: Session = Depends(get_db)):
    timeslot = db.query(TimeSlot).filter(TimeSlot.id == timeslot_id).first()
    if not timeslot:
        raise HTTPException(status_code=404, detail="TimeSlot tidak ditemukan")

    db.delete(timeslot)
    db.commit()
    return {"message": "TimeSlot berhasil dihapus"}
