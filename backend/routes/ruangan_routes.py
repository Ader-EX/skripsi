from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from model.timeslot_model import TimeSlot
from model.timetable_model import TimeTable
from database import get_db
from model.ruangan_model import Ruangan
from pydantic import BaseModel
from typing import Dict, List, Optional
from enum import Enum

router = APIRouter()

# Enums for predefined values
class GedungEnum(str, Enum):
    KHD = "KHD"
    DS = "DS"
    OTHER = "Other"

class GroupCodeEnum(str, Enum):
    KHD2 = "KHD2"
    KHD3 = "KHD3"
    KHD4 = "KHD4"
    DS2 = "DS2"
    DS3 = "DS3"
    DS4 = "DS4"
    OTHER = "Other"

class TipeRuanganEnum(str, Enum):
    P = "P"
    T = "T"
    S = "Ss"

class TipeRuangan(str, Enum):
    P = "P"
    T = "T"
    S = "S"

# Schemas for API requests and responses
class RuanganCreate(BaseModel):
    kode_ruangan: str
    nama_ruang: str
    tipe_ruangan: TipeRuanganEnum
    kapasitas: int
    alamat: Optional[str] = None
    gedung: GedungEnum
    group_code: GroupCodeEnum

class RuanganRead(BaseModel):
    id: int
    kode_ruangan: str
    nama_ruang: str
    tipe_ruangan: str
    
    kapasitas: int
    alamat: Optional[str]
    gedung: Optional[str]
    group_code: Optional[str]

    class Config:
        orm_mode = True

class PaginatedRuangan(BaseModel):
    total: int
    page: int
    page_size: int
    data: List[RuanganRead]

    class Config:
        orm_mode = True

# CRUD Operations
@router.post("/", response_model=RuanganRead, status_code=status.HTTP_201_CREATED)
async def create_ruangan(ruangan: RuanganCreate, db: Session = Depends(get_db)):
    # Check if ruangan already exists
    db_ruangan = db.query(Ruangan).filter(Ruangan.kode_ruangan == ruangan.kode_ruangan).first()
    if db_ruangan:
        raise HTTPException(status_code=400, detail="Ruangan with this kode_ruangan already exists")

    new_ruangan = Ruangan(**ruangan.dict())
    db.add(new_ruangan)
    db.commit()
    db.refresh(new_ruangan)
    return new_ruangan



@router.get("/", response_model=PaginatedRuangan)
async def get_all_ruangan(
    jenis: Optional[str] = Query(None, description="Filter by jenis ruang"),
    name: Optional[str] = Query(None, description="Search by name"),
    gedung: Optional[str] = Query(None, description="Filter by gedung"),
    group_code: Optional[str] = Query(None, description="Filter by group code"),
    page: int = Query(1, description="Page number", gt=0),
    page_size: int = Query(10, description="Page size", gt=0),
    db: Session = Depends(get_db),
):
    query = db.query(Ruangan)
    
    if name:
        query = query.filter(Ruangan.nama_ruang.ilike(f"%{name}%"))
    if gedung and gedung != "Semua":
        query = query.filter(Ruangan.gedung == gedung)
    if group_code and group_code != "Semua":
        query = query.filter(Ruangan.group_code == group_code)
    
    total = query.count()
    ruangan_list = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": ruangan_list
    }



@router.get("/timeslots/availability")
def get_timeslot_availability(
    ruangan_id: int,
    day_index: Optional[int] = None,  # Optional filter by day
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Fetches the availability of timeslots for a specific ruangan (room).
    - `ruangan_id`: The ID of the room
    - `day_index` (optional): If provided, filters timeslots for a specific day.
    """

    # Validate if the room exists
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")

    # Fetch all timeslots, optionally filter by `day_index`
    timeslot_query = db.query(TimeSlot)
    if day_index is not None:
        timeslot_query = timeslot_query.filter(TimeSlot.day_index == day_index)
    timeslots = timeslot_query.all()

    # Fetch all timetables for this `ruangan_id`
    busy_timetables = (
        db.query(TimeTable)
        .filter(TimeTable.ruangan_id == ruangan_id)
        .all()
    )

    # Get a set of busy timeslot IDs
    busy_timeslot_ids = set()
    for timetable in busy_timetables:
        busy_timeslot_ids.update(timetable.timeslot_ids)

    # Format the response
    result = []
    for timeslot in timeslots:
        status = "Busy" if timeslot.id in busy_timeslot_ids else "Free"
        result.append({
            "timeslot_id": timeslot.id,
            "day": timeslot.day.value,  # Convert Enum to string
            "start_time": str(timeslot.start_time),
            "end_time": str(timeslot.end_time),
            "status": status
        })

    return result


@router.get("/{ruangan_id}", response_model=RuanganRead)
async def get_ruangan(ruangan_id: int, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")
    return ruangan

@router.put("/{ruangan_id}", response_model=RuanganRead)
async def update_ruangan(ruangan_id: int, updated_ruangan: RuanganCreate, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")

    for key, value in updated_ruangan.dict().items():
        setattr(ruangan, key, value)

    db.commit()
    db.refresh(ruangan)
    return ruangan

@router.delete("/{ruangan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ruangan(ruangan_id: int, db: Session = Depends(get_db)):
    ruangan = db.query(Ruangan).filter(Ruangan.id == ruangan_id).first()
    if not ruangan:
        raise HTTPException(status_code=404, detail="Ruangan not found")

    db.delete(ruangan)
    db.commit()
    return {"message": "Ruangan deleted successfully"}


