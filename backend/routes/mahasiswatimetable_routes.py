from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from typing import List
from pydantic import BaseModel

from model.mahasiswatimetable_model import MahasiswaTimeTable
from model.mahasiswa_model import Mahasiswa
from model.timetable_model import TimeTable

router = APIRouter()

# Pydantic Models
class MahasiswaTimeTableBase(BaseModel):
    mahasiswa_id: int
    timetable_id: int
    semester: int
    tahun_ajaran: int

class MahasiswaTimeTableCreate(MahasiswaTimeTableBase):
    pass

class MahasiswaTimeTableRead(MahasiswaTimeTableBase):
    id: int
    total_sks: int

    class Config:
        orm_mode = True


# Routes
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

    # Check for duplicate entries
    existing_entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MahasiswaTimeTable.timetable_id == entry.timetable_id
    ).first()

    if existing_entry:
        raise HTTPException(status_code=400, detail="Timetable already added to the mahasiswa's timetable")

    # Calculate total_sks
    previous_sks = db.query(MahasiswaTimeTable.total_sks).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id
    ).order_by(MahasiswaTimeTable.id.desc()).first()
    previous_sks = previous_sks[0] if previous_sks else 0
    total_sks = previous_sks + timetable.sks  # Assuming timetable has an `sks` field

    # Create new entry
    new_entry = MahasiswaTimeTable(
        mahasiswa_id=entry.mahasiswa_id,
        timetable_id=entry.timetable_id,
        semester=entry.semester,
        tahun_ajaran=entry.tahun_ajaran,
        total_sks=total_sks
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@router.get("/{mahasiswa_id}", response_model=List[MahasiswaTimeTableRead])
async def get_timetable_by_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    timetable_entries = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id).all()
    if not timetable_entries:
        raise HTTPException(status_code=200, detail="No timetable entries found for this mahasiswa")
    return timetable_entries


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timetable_entry(entry_id: int, db: Session = Depends(get_db)):
    timetable_entry = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.id == entry_id).first()
    if not timetable_entry:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    db.delete(timetable_entry)

    # Update total_sks for remaining entries
    remaining_entries = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == timetable_entry.mahasiswa_id
    ).order_by(MahasiswaTimeTable.id.asc()).all()
    updated_sks = 0
    for entry in remaining_entries:
        updated_sks += entry.timetable.sks
        entry.total_sks = updated_sks
        db.add(entry)

    db.commit()
    return {"message": "Timetable entry deleted successfully"}


@router.delete("/reset/{mahasiswa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def reset_timetable(mahasiswa_id: int, db: Session = Depends(get_db)):
    timetable_entries = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id).all()
    if not timetable_entries:
        raise HTTPException(status_code=404, detail="No timetable entries found for this mahasiswa")

    for entry in timetable_entries:
        db.delete(entry)

    db.commit()
    return {"message": "Timetable reset successfully"}
