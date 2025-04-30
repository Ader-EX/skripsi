import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from model.mahasiswatimetable_model import MahasiswaTimeTable
from model.ruangan_model import Ruangan
from model.academicperiod_model import AcademicPeriods
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from database import get_db
from model.timetable_model import TimeTable
from model.timeslot_model import TimeSlot
from typing import List
from .algorithm_routes import check_timetable_conflicts




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



@router.post("/resolve-conflicts")
async def resolve_conflicts(db: Session = Depends(get_db)):

    conflicted_entries = db.query(TimeTable).filter(
        TimeTable.is_conflicted == True,
        TimeTable.reason.isnot(None)
    ).order_by(case(
        {"Lecturer Conflict": 3, "Room Conflict": 2, "Timeslot Conflict": 1, "Day Crossing": 0},
        value=TimeTable.reason
    ).desc()).all()
    
    resolved_conflicts = []

    for entry in conflicted_entries:
       
        new_room, new_timeslot_ids = find_new_room_and_timeslot(db, entry)
        
        if new_room and new_timeslot_ids:
            old_room_id = entry.ruangan_id
            old_timeslots = entry.timeslot_ids
            conflict_type = entry.reason
            
            entry.ruangan_id = new_room.id
            entry.timeslot_ids = new_timeslot_ids
            entry.is_conflicted = False  
            entry.reason = None
            
            entry.placeholder = generate_placeholder(db, new_room.id, new_timeslot_ids)
            
            resolved_conflicts.append({
                "timetable_id": entry.id,
                "previous_room": old_room_id,
                "new_room": new_room.id,
                "previous_timeslot": old_timeslots,
                "new_timeslot": new_timeslot_ids,
                "resolved_conflict_type": conflict_type
            })
    
    db.commit()
    
    return {
        "message": "Conflicts berhasil diatasi",
        "resolved_conflicts": resolved_conflicts,
        "total_resolved": len(resolved_conflicts),
        "total_remaining": db.query(TimeTable).filter(TimeTable.is_conflicted == True).count()
    }


def conflict_priority(conflict_type):
    # format prioritas konflik biar yg dihandle dari yang paling penting dlu
    priority_map = {
        "Lecturer Conflict": 3,  
        "Room Conflict": 2,
        "Timeslot Conflict": 1,
        "Day Crossing": 0  
    }
    return priority_map.get(conflict_type, 0)


def find_new_room_and_timeslot(db: Session, timetable_entry: TimeTable):
    #  mencoba seluruh kemungkinan ruangan dan timeslot yang berutuan.  
  

    required_sks = len(timetable_entry.timeslot_ids)
    candidate_rooms = db.query(Ruangan).filter(
        Ruangan.kapasitas >= timetable_entry.kapasitas
    ).all()

    # ambil seluruh timeslot
    all_timeslots = db.query(TimeSlot).order_by(TimeSlot.day_index, TimeSlot.start_time).all()
    grouped_by_day = {}
    for ts in all_timeslots:
        grouped_by_day.setdefault(ts.day_index, []).append(ts)

    # untuk setiap kandidtat ruangan
    for room in candidate_rooms:
        # untuk tiap hari yang ada
        for day_index, timeslots in grouped_by_day.items():
            # geser timeslot untuk mencari yang beututan    # untuk setiap timeslot yang ada di ruangan tersebut
            for i in range(len(timeslots) - required_sks + 1):
                selected_block = timeslots[i : i + required_sks]

                # buat ngecek berutuan engganya
                if not all(ts.day_index == day_index for ts in selected_block):
                    continue

                new_timeslot_ids = [ts.id for ts in selected_block]

                # Cek konflik baru
                if not causes_new_conflict(db, room.id, new_timeslot_ids):
                    return (room, new_timeslot_ids)

    return (None, None)


def causes_new_conflict(db: Session, room_id: int, timeslot_ids: list[int]) -> bool:

    conflict = db.query(TimeTable).filter(
        TimeTable.ruangan_id == room_id,
        func.json_contains(TimeTable.timeslot_ids, json.dumps(timeslot_ids))
    ).first()

    return conflict is not None


def generate_placeholder(db: Session, room_id: int, timeslot_ids: list[int]) -> str:
    """
    Generate placeholder berdasarkan kelas paling atas (biasanya kelas A)
    """
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
    if timeslots:
        first_ts = min(timeslots, key=lambda t: t.start_time)
        last_ts = max(timeslots, key=lambda t: t.end_time)
        return f"1. Ruangan {room_id} - {first_ts.day.value} ({first_ts.start_time} - {last_ts.end_time})"
    return "1. Unknown Room - Unknown slot waktu"

@router.post("/", response_model=TimeTableResponse)
def create_timetable(timetable: TimeTableCreate, db: Session = Depends(get_db)):
    
    existing_class = db.query(TimeTable).filter(TimeTable.opened_class_id == timetable.opened_class_id).first()
    if existing_class:
        raise HTTPException(status_code=400, detail="opened class entri ini sudah ada")

    for timeslot in timetable.timeslot_ids:
        conflict = db.query(TimeTable).filter(
            TimeTable.ruangan_id == timetable.ruangan_id,
            func.json_contains(TimeTable.timeslot_ids, json.dumps([timeslot]))
        ).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Ruangan {timetable.ruangan_id} sudah mengambil timeslot {timeslot}.")

    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise HTTPException(status_code=404, detail="periode akademik aktif tidak ditemukan.")

    academic_period_id = active_period.id

    opened_class = db.query(OpenedClass).filter(OpenedClass.id == timetable.opened_class_id).first()
    if not opened_class:
        raise HTTPException(status_code=404, detail="Opened class tidak ditemukan.")

    kapasitas = opened_class.kapasitas
    kelas = opened_class.kelas  
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timetable.timeslot_ids)).all()
    if timeslots:
        timeslot_str = f"{timetable.ruangan_id} - {timeslots[0].day} ({timeslots[0].start_time} - {timeslots[-1].end_time})"
    else:
        timeslot_str = f"{timetable.ruangan_id} - Unknown TimeSlot"

    selected_class_times = [f"1. {timeslot_str}"]

    mata_kuliah_kodemk = opened_class.mata_kuliah_kodemk
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == mata_kuliah_kodemk).first()

    base_class = db.query(OpenedClass).filter(
        OpenedClass.mata_kuliah_kodemk == mata_kuliah_kodemk
    ).order_by(OpenedClass.kelas).first()
    if base_class:
        base_timetable = db.query(TimeTable).filter(TimeTable.opened_class_id == base_class.id).first()
        if base_timetable:
            base_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(base_timetable.timeslot_ids)).all()
            if base_timeslots:
                base_str = f"{base_timetable.ruangan_id} - {base_timeslots[0].day} ({base_timeslots[0].start_time} - {base_timeslots[-1].end_time})"
                if mata_kuliah and mata_kuliah.tipe_mk == "T":
                    selected_class_times.append(f"2. {base_str}")

  
    placeholder = "\n".join(selected_class_times)

    new_timetable = TimeTable(
        opened_class_id=timetable.opened_class_id,
        ruangan_id=timetable.ruangan_id,
        timeslot_ids=timetable.timeslot_ids,
        is_conflicted=True,  
        kelas=kelas, 
        kapasitas=kapasitas, 
        reason=None,
        academic_period_id=academic_period_id,  
        kuota=0, 
        placeholder=placeholder,
    )

    db.add(new_timetable)
    db.commit()
    db.refresh(new_timetable)
    return new_timetable



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
            raise HTTPException(status_code=404, detail=f"Timeslot tidak ditemukan untuk {day}")

    if room_id:
        query = query.filter(TimeTable.ruangan_id == room_id)

    timetables = query.all()
    if not timetables:
        raise HTTPException(status_code=404, detail="Tidak ditemukan timetables untuk filter yang diminta")

    return timetables




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
            MataKuliah.sks.label("sks"),
            Ruangan.nama_ruang.label("ruangan_nama")
        )
        .first()
    )

    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable tidak ditemukan")

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
        "sks": timetable.sks,
        "ruangan_nama": timetable.ruangan_nama
    }

    return timetable_data

@router.put("/{id}", response_model=TimeTableResponse)
def update_timetable(id: int, updated_timetable: TimeTableUpdate, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable tidak ditemukan")

    
    if updated_timetable.opened_class_id and updated_timetable.opened_class_id != timetable.opened_class_id:
        existing_class = db.query(TimeTable).filter(TimeTable.opened_class_id == updated_timetable.opened_class_id).first()
        if existing_class:
            raise HTTPException(status_code=400, detail="opened class ini sudah memiliki entri")

    
    if updated_timetable.ruangan_id:
        for timeslot in updated_timetable.timeslot_ids or timetable.timeslot_ids:
            conflict = db.query(TimeTable).filter(
                TimeTable.ruangan_id == updated_timetable.ruangan_id,
                func.json_contains(TimeTable.timeslot_ids, json.dumps([timeslot])),
                TimeTable.id != id  
            ).first()
            if conflict:
                raise HTTPException(status_code=400, detail=f"Ruangan {updated_timetable.ruangan_id} sudah digunakan di waktu {timeslot}.")

    
    timeslot_ids = updated_timetable.timeslot_ids or timetable.timeslot_ids
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
    if timeslots:
        timeslot_str = f"{updated_timetable.ruangan_id or timetable.ruangan_id} - {timeslots[0].day} ({timeslots[0].start_time} - {timeslots[-1].end_time})"
    else:
        timeslot_str = f"{updated_timetable.ruangan_id or timetable.ruangan_id} - Unknown TimeSlot"

    selected_class_times = [f"1. {timeslot_str}"]

    
    mata_kuliah_kodemk = timetable.opened_class.mata_kuliah_kodemk
    mata_kuliah = db.query(MataKuliah).filter(MataKuliah.kodemk == mata_kuliah_kodemk).first()

  
    base_class = db.query(OpenedClass).filter(
        OpenedClass.mata_kuliah_kodemk == mata_kuliah_kodemk
    ).order_by(OpenedClass.kelas).first() 

   
    if base_class:
        base_timetable = db.query(TimeTable).filter(TimeTable.opened_class_id == base_class.id).first()
        if base_timetable:
            base_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(base_timetable.timeslot_ids)).all()
            if base_timeslots:
                base_str = f"{base_timetable.ruangan_id} - {base_timeslots[0].day} ({base_timeslots[0].start_time} - {base_timeslots[-1].end_time})"
                if mata_kuliah and mata_kuliah.tipe_mk == "T":
                    selected_class_times.append(f"2. {base_str}")

    
    updated_placeholder = "\n".join(selected_class_times)

    
    for key, value in updated_timetable.dict(exclude_unset=True).items():
        setattr(timetable, key, value)
    timetable.placeholder = updated_placeholder
    timetable.is_conflicted = True
    timetable.reason = None
    db.commit()
    db.refresh(timetable)

    
    if timetable.opened_class.kelas.upper() == base_class.kelas.upper():
        related_timetables = db.query(TimeTable).join(OpenedClass).filter(
            OpenedClass.mata_kuliah_kodemk == mata_kuliah_kodemk,
            OpenedClass.kelas != base_class.kelas
        ).all()
        for other_tt in related_timetables:
            other_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(other_tt.timeslot_ids)).all()
            if other_timeslots:
                other_str = f"{other_tt.ruangan_id} - {other_timeslots[0].day} ({other_timeslots[0].start_time} - {other_timeslots[-1].end_time})"
            else:
                other_str = f"{other_tt.ruangan_id} - Unknown TimeSlot"
            other_selected_class_times = [f"1. {other_str}"]
            if mata_kuliah and mata_kuliah.tipe_mk == "T":
                other_selected_class_times.append(f"2. {base_str}")
            other_tt.placeholder = "\n".join(other_selected_class_times)
            db.add(other_tt)
        db.commit()

    return timetable


@router.delete("/{id}")
def delete_timetable(id: int, db: Session = Depends(get_db)):
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable tidak ditemukan")

  
    db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.timetable_id == id).delete(synchronize_session=False)

    db.delete(timetable)
    db.commit()

    return {"message": "Timetable dan related mahasiswa_timetable entri berhasil dihapus"}

