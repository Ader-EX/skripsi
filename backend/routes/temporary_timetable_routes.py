from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from database import get_db  # Pastikan ada function get_db di database.py
from model.temporary_timetable_model import TemporaryTimeTable

router = APIRouter(
    prefix="/temporary-timetables",
    tags=["Temporary TimeTables"]
)

# ====== SCHEMAS ======

class TemporaryTimeTableBase(BaseModel):
    timetable_id: int
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

# ====== CRUD FUNCTIONS ======

def create_temporary_timetable(db: Session, temp_data: TemporaryTimeTableCreate):
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

    for key, value in temp_data.dict(exclude_unset=True).items():
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
    return create_temporary_timetable(db, temp)

@router.get("/", response_model=List[TemporaryTimeTableResponse])
def get_all_temporary_timetables_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_temporary_timetables(db, skip, limit)

@router.get("/{temp_id}", response_model=TemporaryTimeTableResponse)
def get_temporary_timetable_endpoint(temp_id: int, db: Session = Depends(get_db)):
    db_temp = get_temporary_timetable_by_id(db, temp_id)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable not found")
    return db_temp

@router.put("/{temp_id}", response_model=TemporaryTimeTableResponse)
def update_temporary_timetable_endpoint(temp_id: int, temp: TemporaryTimeTableUpdate, db: Session = Depends(get_db)):
    db_temp = update_temporary_timetable(db, temp_id, temp)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable not found")
    return db_temp

@router.delete("/{temp_id}")
def delete_temporary_timetable_endpoint(temp_id: int, db: Session = Depends(get_db)):
    db_temp = delete_temporary_timetable(db, temp_id)
    if not db_temp:
        raise HTTPException(status_code=404, detail="Temporary timetable not found")
    return {"detail": "Temporary timetable deleted"}
