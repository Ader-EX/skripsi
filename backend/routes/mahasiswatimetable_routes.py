from fastapi import APIRouter, Depends, HTTPException, Query, logger, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from model.dosen_model import Dosen
from model.timeslot_model import TimeSlot
from model.matakuliah_programstudi import MataKuliahProgramStudi
from model.openedclass_model import OpenedClass
from model.matakuliah_model import MataKuliah
from database import get_db
from typing import Any, Dict, List, Optional
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

    # Get the OpenedClass associated with the timetable
    opened_class = db.query(OpenedClass).filter(OpenedClass.id == timetable.opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened Class not found")

    # Get the MataKuliahProgramStudi associated with the OpenedClass
    mata_kuliah_program_studi = db.query(MataKuliahProgramStudi).filter(
        MataKuliahProgramStudi.id == opened_class.mata_kuliah_program_studi_id
    ).first()
    if not mata_kuliah_program_studi:
        raise HTTPException(status_code=404, detail="Mata Kuliah Program Studi not found")

    # Retrieve the MataKuliah associated with the MataKuliahProgramStudi
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == mata_kuliah_program_studi.mata_kuliah_id).first()
    if not mata_kuliah:
        raise HTTPException(status_code=404, detail="Mata Kuliah not found")

    # Check for duplicate entries
    existing_entry = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.mahasiswa_id == entry.mahasiswa_id,
        MahasiswaTimeTable.timetable_id == entry.timetable_id
    ).first()

    if existing_entry:
        raise HTTPException(status_code=400, detail="Timetable already added to the mahasiswa's timetable")

    # Check if the class is full
    current_enrollment = db.query(MahasiswaTimeTable).filter(
        MahasiswaTimeTable.timetable_id == entry.timetable_id
    ).count()

    if current_enrollment >= timetable.kapasitas:
        raise HTTPException(status_code=400, detail="Class is full, cannot add more students")

    # Update the Mahasiswa's sks_diambil
    mahasiswa.sks_diambil += mata_kuliah.sks  # Add the SKS from MataKuliah
    db.commit()  # Commit the update to Mahasiswa

    # Create a new MahasiswaTimeTable entry
    new_entry = MahasiswaTimeTable(
        mahasiswa_id=entry.mahasiswa_id,
        timetable_id=entry.timetable_id,
        semester=entry.semester,
        tahun_ajaran=entry.tahun_ajaran
    )
    db.add(new_entry)
    db.commit()  # Commit the new entry
    db.refresh(new_entry)  # Refresh to get the latest data

    return new_entry






@router.get("/{mahasiswa_id}", response_model=List[MahasiswaTimeTableRead])
async def get_timetable_by_mahasiswa(mahasiswa_id: int, db: Session = Depends(get_db)):
    # Query for timetable entries
    timetable_entries = db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id).all()
    
    # Log the retrieved entries for debugging
    print(f"Retrieved timetable entries for mahasiswa_id {mahasiswa_id}: {timetable_entries}")

    # Check if any entries were found
    if not timetable_entries:
        raise HTTPException(status_code=404, detail="No timetable entries found for this mahasiswa")

    # Optionally, you can return the sks_diambil from the Mahasiswa model
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if mahasiswa:
        for entry in timetable_entries:
            entry.sks_diambil = mahasiswa.sks_diambil  # Add sks_diambil to each entry if needed

    return timetable_entries


@router.get("/timetable/{mahasiswa_id}", response_model=Dict[str, Any])
async def get_timetable_by_mahasiswa(
    mahasiswa_id: int,
    db: Session = Depends(get_db),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk")
):
    # Check if Mahasiswa exists
    mahasiswa = db.query(Mahasiswa).filter(Mahasiswa.id == mahasiswa_id).first()
    if not mahasiswa:
        raise HTTPException(status_code=404, detail="Mahasiswa not found")

    try:
        # Base query optimized for MySQL (including title_depan & title_belakang)
        query = db.query(
            TimeTable.id, 
            TimeTable.opened_class_id,
            TimeTable.ruangan_id,
            TimeTable.timeslot_ids,
            TimeTable.kelas,
            TimeTable.kapasitas,
            TimeTable.kuota,
            OpenedClass.mata_kuliah_program_studi,
            MataKuliah.kodemk,
            MataKuliah.namamk,
            MataKuliah.kurikulum,
            MataKuliah.sks,
            MataKuliah.smt,
            func.group_concat(
                func.concat_ws(" ", Dosen.title_depan, Dosen.nama, Dosen.title_belakang)
                .distinct()
                .op('SEPARATOR')('||')
            ).label("dosen_names")  # Properly formatted dosen names
        ).join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_program_studi.has(mata_kuliah_id=MataKuliah.kodemk)) \
         .join(Dosen, OpenedClass.dosens) \
         .join(MahasiswaTimeTable, MahasiswaTimeTable.timetable_id == TimeTable.id) \
         .filter(MahasiswaTimeTable.mahasiswa_id == mahasiswa_id) \
         .group_by(TimeTable.id, OpenedClass.id, MataKuliah.kodemk, MataKuliah.namamk, MataKuliah.kurikulum, MataKuliah.sks, MataKuliah.smt)

        # Apply filter if provided
        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )

        # Fetch the data
        timetable_data = query.all()

        # Fetch timeslot details in a single query
        timeslot_ids = set(
            ts_id for entry in timetable_data for ts_id in entry.timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        # Format the data
        formatted_timetable = []
        for entry in timetable_data:
            # Format Dosen names into a numbered list
            if entry.dosen_names:
                dosen_list = entry.dosen_names.split("||")
                formatted_dosen = "\n".join([f"{i+1}. {dosen.strip()}" for i, dosen in enumerate(dosen_list)])
            else:
                formatted_dosen = "-"

            # Format timeslots
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
                "dosen": formatted_dosen,  # Now properly formatted with titles
                "timeslots": formatted_timeslots,  # Includes full timeslot details
            }
            formatted_timetable.append(formatted_entry)

        return {
            "mahasiswa_id": mahasiswa_id,
            "data": formatted_timetable,
        }

    except Exception as e:
        logger.error(f"Error fetching timetable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
