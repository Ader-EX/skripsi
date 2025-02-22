import string
from typing import Any, Dict, List, Optional
from numpy import number
from sqlalchemy import String, and_, case, or_, text
from sqlalchemy.orm import Session
# from model.matakuliah_programstudi import MataKuliahProgramStudi
from model.academicperiod_model import AcademicPeriods
from model.user_model import User
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass
from model.timetable_model import TimeTable
from model.openedclass_model import openedclass_dosen
import random
import logging
import time
import math



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)



def clear_timetable(db: Session):
    """Deletes all entries in the timetable table."""
    logger.debug("Clearing all entries in the timetable table...")
    db.query(TimeTable).delete()
    db.commit()
    logger.debug("Timetable cleared successfully.")


def fetch_data(db: Session):
    """
    Fetch all required data for scheduling.
    Ensures timeslots are correctly sorted, including "Senin".
    """
    courses = db.query(MataKuliah).all()
    lecturers = db.query(Dosen).all()
    rooms = db.query(Ruangan).all()
    
    # ✅ Ensure timeslots are fetched in correct order (Senin first)
    timeslots = db.query(TimeSlot).order_by(TimeSlot.day_index, TimeSlot.start_time).all()

    preferences = db.query(Preference).all()
    opened_classes = db.query(OpenedClass).all()

    # Cache mappings for faster access
    opened_class_cache = {oc.id: {
        "mata_kuliah": oc.mata_kuliah,
        "sks": oc.mata_kuliah.sks,
        "dosen_ids": [d.pegawai_id for d in oc.dosens],
        "kelas": oc.kelas,
        "kapasitas": oc.kapasitas
    } for oc in opened_classes}

    room_cache = {r.id: r for r in rooms}
    timeslot_cache = {t.id: t for t in timeslots}

    return courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache











def clear_timetable(db: Session):
    """Deletes all entries in the timetable table."""
    db.execute(text("DELETE FROM mahasiswa_timetable"))
    db.execute(text("DELETE FROM timetable"))
    db.commit()


from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db

router = APIRouter()


from sqlalchemy import func
from typing import List, Dict

from sqlalchemy import func

from sqlalchemy import func
from sqlalchemy.orm import joinedload


def format_timetable(timetable: TimeTable) -> dict:
    return {
        "id": timetable.id,
        "subject": {
            "code": timetable.opened_class.mata_kuliah.kodemk,  # ✅ Corrected reference
            "name": timetable.opened_class.mata_kuliah.namamk
        },
        "class": timetable.opened_class.kelas,  # ✅ Class info comes from OpenedClass
        "room": {
            "id": timetable.ruangan.id,
            "code": timetable.ruangan.kode_ruangan,
            "name": timetable.ruangan.nama_ruang,
            "capacity": timetable.ruangan.kapasitas
        },
        "lecturers": [
            {
                "id": dosen.pegawai_id,
                "name": dosen.nama  # ✅ Fetch fullname from User table
            }
            for dosen in timetable.opened_class.dosens
        ],
        "capacity": timetable.opened_class.kapasitas,
        "enrolled": timetable.kuota,
        "is_conflicted": timetable.is_conflicted,
        "timeslots": [
            {
                "id": ts.id,
                "day": ts.day,
                "startTime": ts.start_time.strftime("%H:%M"),
                "endTime": ts.end_time.strftime("%H:%M")
            }
            for ts in timetable.timeslots
        ]
    }



from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import time
from pydantic import BaseModel
from typing import List



class TimeSlotBase(BaseModel):
    day: str
    start_time: time
    end_time: time

class TimeTableCreate(BaseModel):
    subject_id: int
    class_name: str
    lecturer_ids: List[int]
    timeslots: List[TimeSlotBase]
    room_id: int
    capacity: int
    enrolled: int

from sqlalchemy import desc



@router.delete("/reset-schedule")
async def reset_schedule(db: Session = Depends(get_db)):
    try:
        clear_timetable(db)
        return {"message": "Schedule reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy.orm import joinedload
from sqlalchemy import or_, desc
from fastapi import HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional



@router.get("/formatted-timetable")
async def get_timetable(
    db: Session = Depends(get_db),
    is_conflicted: Optional[bool] = Query(None, description="Filter by conflict status"),
    program_studi_id: Optional[str] = Query(None, description="Filter by program studi id"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    filterText: Optional[str] = Query(None, description="Filter by subject or lecturer")
):
    try:
        active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
        if not active_period:
            raise HTTPException(status_code=404, detail="Periode akademik aktif tidak ditemukan.")

        # Base query with joinedload for efficient relationship loading
        query = db.query(TimeTable).options(
            joinedload(TimeTable.opened_class).joinedload(OpenedClass.mata_kuliah),
            joinedload(TimeTable.ruangan),
            joinedload(TimeTable.opened_class).joinedload(OpenedClass.dosens),
        ).filter(TimeTable.academic_period_id == active_period.id)

        # Filter by conflict status if provided
        if is_conflicted is not None:
            query = query.filter(TimeTable.is_conflicted == is_conflicted)

        # If filtering by program_studi_id or filterText, join necessary tables
        if program_studi_id is not None or filterText:
            query = query.join(OpenedClass).join(MataKuliah)

        
        if program_studi_id is not None:
            query = query.filter(MataKuliah.program_studi_id == program_studi_id)

        # Apply search filter if provided
        if filterText:
            search_term = f"%{filterText}%"
            query = query.join(OpenedClass.dosens).filter(
                or_(
                    MataKuliah.namamk.ilike(search_term),
                    MataKuliah.kodemk.ilike(search_term),
                    Dosen.nama.ilike(search_term)
                )
            ).distinct()

        # Custom ordering:
        # 1. Entries with is_conflicted True and reason not null
        # 2. Entries with is_conflicted True and reason null
        # 3. Other entries
        conflict_order = case(
            (and_(TimeTable.is_conflicted == True, TimeTable.reason.isnot(None)), 1),
            (and_(TimeTable.is_conflicted == True, TimeTable.reason.is_(None)), 2),
            else_=3
        )
        query = query.order_by(
            desc(TimeTable.is_conflicted),
            TimeTable.reason.is_(None),  # False (i.e. not NULL) sorts before True (NULL)
            TimeTable.id
        )

        # Get total record count before pagination
        total_records = query.count()

        # Apply pagination
        timetables = query.offset((page - 1) * limit).limit(limit).all()

        formatted_data = []
        for timetable in timetables:
            opened_class = timetable.opened_class
            mata_kuliah = opened_class.mata_kuliah
            dosens = opened_class.dosens
            room = timetable.ruangan

            # Get timeslots
            timeslot_ids = timetable.timeslot_ids
            timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()

            formatted_data.append({
                "id": timetable.id,
                "subject": {
                    "code": mata_kuliah.kodemk,
                    "name": mata_kuliah.namamk,
                    "sks": mata_kuliah.sks,
                    "semester": mata_kuliah.smt
                },
                "class": opened_class.kelas,
                "lecturers": [
                    {
                        "id": d.pegawai_id,
                        "name": f"{d.title_depan or ''} {d.nama} {d.title_belakang or ''}".strip()
                    } for d in dosens
                ],
                "timeslots": [
                    {
                        "id": t.id,
                        "day": t.day,
                        "startTime": str(t.start_time),
                        "endTime": str(t.end_time)
                    } for t in timeslots
                ],
                "room": {
                    "id": room.id,
                    "code": room.kode_ruangan,
                    "capacity": room.kapasitas
                },
                "capacity": timetable.kapasitas,
                "enrolled": timetable.kuota,
                "is_conflicted": timetable.is_conflicted,
                "reason": timetable.reason,
                "is_active": active_period.is_active,
                "placeholder": timetable.placeholder
            })

        metadata = {
            "semester": f"{active_period.tahun_ajaran} - Semester {active_period.semester}",
            "week_start": str(active_period.start_date),
            "week_end": str(active_period.end_date),
            "is_active": active_period.is_active
        }

        return {
            "metadata": metadata,
            "data": formatted_data,
            "total_pages": (total_records + limit - 1) // limit,
            "current_page": page,
            "total_records": total_records
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timetable: {str(e)}")



@router.post("/formatted-timetable")
async def create_timetable(
    timetable: TimeTableCreate,
    db: Session = Depends(get_db)
):
    try:
        # Create new timetable entry
        new_timetable = TimeTable(
            kapasitas=timetable.capacity,
            kuota=timetable.enrolled,
            ruangan_id=timetable.room_id
        )
        
        # Create opened class
        opened_class = OpenedClass(
            mata_kuliah_id=timetable.subject_id,
            kelas=timetable.class_name
        )
        
        # Add lecturers
        lecturers = db.query(Dosen).filter(Dosen.id.in_(timetable.lecturer_ids)).all()
        opened_class.dosens.extend(lecturers)
        
        # Create timeslots
        timeslots = []
        for ts in timetable.timeslots:
            timeslot = TimeSlot(
                day=ts.day,
                start_time=ts.start_time,
                end_time=ts.end_time
            )
            db.add(timeslot)
            timeslots.append(timeslot)
        
        db.flush()  # Get IDs for timeslots
        new_timetable.timeslot_ids = [t.id for t in timeslots]
        
        # Check for conflicts
        new_timetable.is_conflicted = check_for_conflicts(db, new_timetable)
        
        db.add(new_timetable)
        db.commit()
        
        return {"message": "Timetable created successfully", "id": new_timetable.id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating timetable: {str(e)}")

def check_for_conflicts(db: Session, timetable: TimeTable) -> bool:
    """
    Check if the given timetable has any conflicts with existing timetables.
    Returns True if conflicts exist, False otherwise.
    """
    # Get all timeslots for the current timetable
    current_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timetable.timeslot_ids)).all()
    
    # Get all other timetables
    other_timetables = db.query(TimeTable).filter(TimeTable.id != timetable.id).all()
    
    for other_timetable in other_timetables:
        other_timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(other_timetable.timeslot_ids)).all()
        
        # Check for room conflicts
        if timetable.ruangan_id == other_timetable.ruangan_id:
            for current_ts in current_timeslots:
                for other_ts in other_timeslots:
                    if current_ts.day == other_ts.day:
                        # Check if time periods overlap
                        if (current_ts.start_time < other_ts.end_time and 
                            current_ts.end_time > other_ts.start_time):
                            return True
        
        # Check for lecturer conflicts
        current_lecturer_ids = {d.id for d in timetable.opened_class.dosens}
        other_lecturer_ids = {d.id for d in other_timetable.opened_class.dosens}
        
        if current_lecturer_ids.intersection(other_lecturer_ids):
            for current_ts in current_timeslots:
                for other_ts in other_timeslots:
                    if current_ts.day == other_ts.day:
                        if (current_ts.start_time < other_ts.end_time and 
                            current_ts.end_time > other_ts.start_time):
                            return True
    
    return False


from typing import Optional
from fastapi import HTTPException, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

@router.get("/timetable-view/")
async def get_timetable_view(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by course name or code"),
    show_conflicts: bool = Query(False, description="Include conflict reasons in response")
):
    # Fetch only ONE active academic period (e.g., the latest one)
    active_academic_period = (
        db.query(AcademicPeriods)
        .filter(AcademicPeriods.is_active == True)
        .order_by(AcademicPeriods.start_date.desc())  # Ensure it's the most recent one
        .first()
    )

    if not active_academic_period:
        raise HTTPException(status_code=404, detail="No active academic period found")

    timetables_query = (
        db.query(TimeTable)
        .join(TimeTable.opened_class)
        .join(OpenedClass.mata_kuliah)
        .join(TimeTable.ruangan)
        .join(OpenedClass.dosens)
        .join(Dosen.user)
        .filter(TimeTable.academic_period_id == active_academic_period.id)
    )

    if search:
        search_term = f"%{search}%"
        timetables_query = timetables_query.filter(
            or_(
                MataKuliah.namamk.ilike(search_term),
                MataKuliah.kodemk.ilike(search_term)
            )
        )

    timetables = timetables_query.all()
    time_slots = db.query(TimeSlot).all()
    rooms = db.query(Ruangan).all()

    metadata = {
        "semester": f"{active_academic_period.tahun_ajaran} - Semester {active_academic_period.semester}",
        "week_start": f"{active_academic_period.start_date}",
        "week_end": f"{active_academic_period.end_date}"
    }

    time_slots_data = [
        {
            "id": ts.id,
            "day": ts.day.value,
            "start_time": ts.start_time.strftime("%H:%M"),
            "end_time": ts.end_time.strftime("%H:%M")
        }
        for ts in time_slots
    ]

    rooms_data = [
        {
            "id": room.kode_ruangan,
            "name": room.nama_ruang,
            "building": room.gedung,
            "floor": room.group_code,
            "capacity": room.kapasitas,
        }
        for room in rooms
    ]

    schedules_data = [
        {
            "id": f"SCH{timetable.id}",
            "subject": {
                "code": timetable.opened_class.mata_kuliah.kodemk,
                "name": timetable.opened_class.mata_kuliah.namamk,
                "kelas": timetable.opened_class.kelas,
            },
            "room_id": timetable.ruangan.kode_ruangan,
            "lecturers": [
                {
                    "id": str(dosen.pegawai_id),
                    "name": dosen.nama,
                    "title_depan": dosen.title_depan,
                    "title_belakang": dosen.title_belakang
                }
                for dosen in timetable.opened_class.dosens
            ],
            "time_slots": [
                {
                    "id" : ts.id,
                    "day": ts.day,
                    "day_index": ts.day_index,
                    "start_time": ts.start_time.strftime("%H:%M"),
                    "end_time": ts.end_time.strftime("%H:%M")
                }
                for ts in timetable.timeslots
            ],
            "student_count": timetable.kuota,
            "max_capacity": timetable.opened_class.kapasitas,
            "academic_year": active_academic_period.tahun_ajaran,
            "semester_period": active_academic_period.semester,
            "is_conflicted": timetable.is_conflicted,
            "reason": timetable.reason if timetable.is_conflicted else None
        }
        for timetable in timetables
    ]

    filters = {
        "available_days": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"],
        "available_times": {
            "start": "07:10",
            "end": "18:00",
            "interval": 50
        },
        "buildings": ["KHD", "DS", "OTH"],
        "class_types": ["T", "P", "S"]
    }

    return {
        "metadata": metadata,
        "time_slots": time_slots_data,
        "rooms": rooms_data,
        "schedules": schedules_data,
        "filters": filters
    }



@router.get("/timetable", response_model=Dict[str, Any])
async def get_timetable(
    db: Session = Depends(get_db),
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(20, description="Number of items per page", ge=1, le=100),
    filter: Optional[str] = Query(None, description="Filter by Mata Kuliah name or Kodemk")
):
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
            OpenedClass.mata_kuliah_kodemk,
            MataKuliah.kodemk,
            MataKuliah.namamk,
            MataKuliah.kurikulum,
            MataKuliah.sks,
            MataKuliah.smt,
            func.group_concat(
                func.concat_ws(" ", Dosen.title_depan, Dosen.nama, Dosen.title_belakang)
                .distinct()
                .op('SEPARATOR')('||')
            ).label("dosen_names")  # ✅ Properly formatted dosen names
        ).join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_kodemk == MataKuliah.kodemk) \
         .join(Dosen, OpenedClass.dosens) \
         .group_by(TimeTable.id, OpenedClass.id, MataKuliah.kodemk, MataKuliah.namamk, MataKuliah.kurikulum, MataKuliah.sks, MataKuliah.smt)

        # Apply filter
        if filter:
            query = query.filter(
                or_(
                    MataKuliah.namamk.ilike(f"%{filter}%"),
                    MataKuliah.kodemk.ilike(f"%{filter}%")
                )
            )

        # Get total count before pagination
        total_records = db.query(func.count()).select_from(query.subquery()).scalar()
        total_pages = (total_records + limit - 1) // limit

        # Fetch paginated data
        timetable_data = query.offset((page - 1) * limit).limit(limit).all()

        # Fetch timeslot details in a single query
        timeslot_ids = set(
            ts_id for entry in timetable_data for ts_id in entry.timeslot_ids if ts_id
        )
        timeslot_map = {
            ts.id: ts for ts in db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
        }

        # Format the data
        formatted_timetable = []
        for idx, entry in enumerate(timetable_data, start=(page - 1) * limit + 1):
            # ✅ Format Dosen names into a numbered list
            if entry.dosen_names:
                dosen_list = entry.dosen_names.split("||")
                formatted_dosen = "\n".join([f"{i+1}. {dosen.strip()}" for i, dosen in enumerate(dosen_list)])
            else:
                formatted_dosen = "-"

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
                "no": idx,
                "kodemk": entry.kodemk,
                "matakuliah": entry.namamk,
                "kurikulum": entry.kurikulum,
                "kelas": entry.kelas,
                "kap_peserta": f"{entry.kapasitas} / {entry.kuota}",
                "sks": entry.sks,
                "smt": entry.smt,
                "dosen": formatted_dosen,  # ✅ Now properly formatted with titles
                "timeslots": formatted_timeslots,  # ✅ Includes full timeslot details
            }
            formatted_timetable.append(formatted_entry)

        return {
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": formatted_timetable,
        }

    except Exception as e:
        logger.error(f"Error fetching timetable: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List, Dict, Tuple


def check_conflicts(db: Session,
                    solution,
                    opened_class_cache,
                    room_cache,
                    timeslot_cache):
    """
    Pengecekan konflik untuk penugasan jadwal.

    - Memperbarui field `is_conflicted` dan `reason` pada tabel TimeTable.
    - Jika sebuah entry sudah memiliki alasan konflik (reason tidak null),
      biarkan tetap tercatat (is_conflicted = 1) meskipun pengecekan ulang dijalankan.
    """
    conflict_details = []
    timeslot_usage = {}
    lecturer_schedule = {}
    conflicted_timetable_ids = set()

    # Reset hanya entry yang TIDAK memiliki alasan konflik yang tersimpan
    db.query(TimeTable).filter(TimeTable.reason.is_(None)).update(
        {"is_conflicted": 0}, synchronize_session=False
    )

    for assignment in solution:
        opened_class_id, room_id, timeslot_id = assignment

        # Dapatkan entry TimeTable yang sesuai
        timetable_entry = db.query(TimeTable).filter(
            TimeTable.opened_class_id == opened_class_id,
            TimeTable.timeslot_ids[0] == timeslot_id
        ).first()
        if not timetable_entry:
            continue

        class_info = opened_class_cache[opened_class_id]
        sks = class_info["sks"]
        current_mk_name = class_info["mata_kuliah"].namamk
        current_kelas = class_info["kelas"]

        current_timeslot = timeslot_cache[timeslot_id]
        current_day_str = (current_timeslot.day.value 
                           if hasattr(current_timeslot.day, "value") 
                           else current_timeslot.day)

        for i in range(sks):
            current_id = timeslot_id + i

            # Timeslot validity check
            if current_id not in timeslot_cache:
                reason = f"Timeslot {current_id} tidak ada"
                conflict_details.append({
                    "type": "Invalid Timeslot",
                    "timetable_id": timetable_entry.id,
                    "opened_class": f"{current_mk_name} - {current_kelas}",
                    "reason": reason,
                    "severity": "High"
                })
                conflicted_timetable_ids.add(timetable_entry.id)
                timetable_entry.is_conflicted = 1
                timetable_entry.reason = reason
                continue

            next_timeslot = timeslot_cache[current_id]
            next_day_str = (next_timeslot.day.value 
                            if hasattr(next_timeslot.day, "value") 
                            else next_timeslot.day)
            start_str = next_timeslot.start_time.strftime("%H:%M")
            end_str = next_timeslot.end_time.strftime("%H:%M")

            # Day crossing check
            if next_day_str != current_day_str:
                reason = f"Kelas melintasi beberapa hari (dari {current_day_str} ke {next_day_str})"
                conflict_details.append({
                    "type": "Day Crossing",
                    "timetable_id": timetable_entry.id,
                    "opened_class": f"{current_mk_name} - {current_kelas}",
                    "reason": reason,
                    "severity": "High"
                })
                conflicted_timetable_ids.add(timetable_entry.id)
                timetable_entry.is_conflicted = 1
                timetable_entry.reason = reason
                continue

            # Room conflict check
            # (Omitted for brevity; same logic as your existing code.)

            # Lecturer conflict check
            for dosen_id in class_info["dosen_ids"]:
                schedule_key = (dosen_id, current_id)
                if schedule_key in lecturer_schedule:
                    # Get the conflict class info
                    conflict_class_id, conflict_timetable_id = lecturer_schedule[schedule_key]
                    conflict_class_info = opened_class_cache[conflict_class_id]
                    conflict_mk_name = conflict_class_info["mata_kuliah"].namamk
                    conflict_kelas = conflict_class_info["kelas"]

                    # Direct DB lookup for the dosen's name
                    dosen = db.query(Dosen).filter(Dosen.pegawai_id == dosen_id).first()
                    dosen_name = dosen.nama if dosen else f"Dosen {dosen_id}"

                    reason = (
                        f"{dosen_name} mengajar kelas {conflict_mk_name} - {conflict_kelas} "
                        f"dan {current_mk_name} - {current_kelas} "
                        f"pada timeslot {next_day_str} ({start_str} - {end_str})"
                    )

                    conflict_details.append({
                        "type": "Lecturer Conflict",
                        "timetable_id": timetable_entry.id,
                        "conflicting_timetable_id": conflict_timetable_id,
                        "opened_class": f"{current_mk_name} - {current_kelas}",
                        "conflicting_opened_class": f"{conflict_mk_name} - {conflict_kelas}",
                        "dosen_id": dosen_id,   
                        "dosen_name": dosen_name,
                        "timeslot": f"{next_day_str} ({start_str} - {end_str})",
                        "reason": reason
                    })
                    conflicted_timetable_ids.add(timetable_entry.id)
                    timetable_entry.is_conflicted = 1
                    timetable_entry.reason = reason

                # Record that this lecturer is teaching this class in this timeslot
                lecturer_schedule[schedule_key] = (opened_class_id, timetable_entry.id)

    # Reset entries not flagged as conflicted
    db.query(TimeTable).filter(
        TimeTable.id.notin_(conflicted_timetable_ids)
    ).update({"is_conflicted": 0, "reason": None}, synchronize_session=False)

    db.commit()

    return {
        "total_conflicts": len(conflicted_timetable_ids),
        "conflict_details": conflict_details
    }


@router.get("/check-conflicts")
async def check_timetable_conflicts(db: Session = Depends(get_db)):
    """
    API Endpoint to check timetable conflicts and update is_conflicted status.
    """
    # Fetch required data
    _, _, _, _, _, _, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)

    # Fetch the current timetable from the database
    timetable = db.query(TimeTable).all()

    # Convert timetable to solution format
    solution = [(entry.opened_class_id, entry.ruangan_id, entry.timeslot_ids[0]) for entry in timetable]

    

    # Check conflicts
    conflict_result = check_conflicts(db, solution, opened_class_cache, room_cache, timeslot_cache)

    return {
        "total_conflicts": conflict_result['total_conflicts'],
        "conflict_details": conflict_result['conflict_details']
    }


@router.get("/formatted-timetable/{timetable_id}")
async def get_timetable_by_id(
    timetable_id: int,
    db: Session = Depends(get_db)
):
    try:
        timetable = (
            db.query(TimeTable)
            .options(
                joinedload(TimeTable.opened_class)
                .joinedload(OpenedClass.mata_kuliah),
                joinedload(TimeTable.ruangan),
                joinedload(TimeTable.opened_class)
                .joinedload(OpenedClass.dosens),
            )
            .filter(TimeTable.id == timetable_id)
            .first()
        )

        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")

        opened_class = timetable.opened_class
        mata_kuliah = opened_class.mata_kuliah
        dosens = opened_class.dosens
        room = timetable.ruangan

        # Get timeslots
        timeslot_ids = timetable.timeslot_ids
        timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()

        formatted_data = {
            "id": timetable.id,
            "opened_class_id": opened_class.id,  # ✅ Include Opened Class ID
            "subject": {
                "code": mata_kuliah.kodemk,
                "name": mata_kuliah.namamk,
                "sks" : mata_kuliah.sks
            },
            "class": opened_class.kelas,
            "lecturers": [{"id": d.pegawai_id, "name": d.nama} for d in dosens],
            "timeslots": [
                {
                    "id": t.id,
                    "day": t.day,
                    "startTime": str(t.start_time),
                    "endTime": str(t.end_time)
                } for t in timeslots
            ],
            "room": {
                "id": room.id,
                "code": room.kode_ruangan,
                "capacity": room.kapasitas
            },
            "capacity": timetable.kapasitas,
            "enrolled": timetable.kuota,
            "is_conflicted": timetable.is_conflicted
        }

        return formatted_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timetable: {str(e)}")




@router.put("/formatted-timetable/{timetable_id}")
async def update_timetable(
    timetable_id: int,
    timetable: TimeTableCreate,
    db: Session = Depends(get_db)
):
    try:
        # Get existing timetable
        existing_timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
        if not existing_timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")

        # Update basic fields
        existing_timetable.kapasitas = timetable.capacity
        existing_timetable.kuota = timetable.enrolled
        existing_timetable.ruangan_id = timetable.room_id

        # Update opened class
        opened_class = existing_timetable.opened_class
        opened_class.mata_kuliah_id = timetable.subject_id
        opened_class.kelas = timetable.class_name

        # Update lecturers
        opened_class.dosens = []  # Clear existing lecturers
        new_lecturers = db.query(Dosen).filter(Dosen.id.in_(timetable.lecturer_ids)).all()
        opened_class.dosens.extend(new_lecturers)

        # Update timeslots
        # First, delete existing timeslots
        db.query(TimeSlot).filter(TimeSlot.id.in_(existing_timetable.timeslot_ids)).delete()
        
        # Create new timeslots
        new_timeslots = []
        for ts in timetable.timeslots:
            timeslot = TimeSlot(
                day=ts.day,
                start_time=ts.start_time,
                end_time=ts.end_time
            )
            db.add(timeslot)
            new_timeslots.append(timeslot)
        
        db.flush()  # Get IDs for new timeslots
        existing_timetable.timeslot_ids = [t.id for t in new_timeslots]
        
        # Check for conflicts
        existing_timetable.is_conflicted = check_for_conflicts(db, existing_timetable)
        
        db.commit()
        return {"message": "Timetable updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating timetable: {str(e)}")

@router.delete("/formatted-timetable/{timetable_id}")
async def delete_timetable(
    timetable_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Get existing timetable
        timetable = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
        if not timetable:
            raise HTTPException(status_code=404, detail="Timetable not found")

        # Delete associated timeslots
        db.query(TimeSlot).filter(TimeSlot.id.in_(timetable.timeslot_ids)).delete()
        
        # Delete the timetable
        db.delete(timetable)
        db.commit()
        
        return {"message": "Timetable deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting timetable: {str(e)}")
