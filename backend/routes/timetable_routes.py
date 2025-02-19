import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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




# @router.post("/resolve-conflicts")
# async def resolve_conflicts(db: Session = Depends(get_db)):
#     """
#     Smart conflict resolution that:
#     - Resolves the most severe conflicts first.
#     - Ensures no new conflicts are created.
#     - Rolls back changes if conflicts remain after resolution.
#     """

#     from .algorithm_routes import check_timetable_conflicts

#     # ✅ Step 1: Fetch existing conflicts
#     conflict_response = await check_timetable_conflicts(db)
#     conflicts = conflict_response.get("conflict_details", [])

#     resolved_conflicts = []

#     for conflict in sorted(conflicts, key=lambda x: conflict_priority(x["type"])):
#         timetable_id = conflict["timetable_id"]
#         conflict_type = conflict["type"]

#         # ✅ Fetch the conflicting timetable entry
#         timetable_entry = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
#         if not timetable_entry:
#             continue  # Skip if timetable not found

#         # ✅ Step 2: Try finding a new available room first
#         new_room = find_available_room(db, timetable_entry)
#         if new_room:
#             new_timeslot_ids = timetable_entry.timeslot_ids  # Keep existing timeslot
#         else:
#             # ✅ Step 3: If no new room, try a new timeslot
#             new_timeslot_ids = find_available_consecutive_timeslots(db, timetable_entry, timetable_entry.ruangan_id)

#         # ✅ Step 4: Verify no new conflicts are introduced
#         if new_room and new_timeslot_ids:
#             if not causes_new_conflict(db, new_room.id, new_timeslot_ids):
#                 # ✅ Apply changes if it's a safe move
#                 timetable_entry.ruangan_id = new_room.id
#                 timetable_entry.timeslot_ids = new_timeslot_ids
#                 timetable_entry.is_conflicted = False
#                 timetable_entry.reason = None  # Conflict resolved

#                 # ✅ Generate placeholder
#                 new_placeholder = generate_placeholder(db, new_room.id, new_timeslot_ids)
#                 timetable_entry.placeholder = new_placeholder

#                 resolved_conflicts.append({
#                     "timetable_id": timetable_entry.id,
#                     "previous_timeslot": conflict.get("timeslot_id"),
#                     "new_timeslot": new_timeslot_ids,
#                     "previous_room": timetable_entry.ruangan_id,
#                     "new_room": new_room.id,
#                     "resolved_conflict_type": conflict_type
#                 })
#             else:
#                 continue  # Skip if the move creates new conflicts

#     # ✅ Commit only if no new conflicts were created
#     db.commit()

#     return {
#         "message": "Conflicts resolved successfully",
#         "resolved_conflicts": resolved_conflicts
#     }


# def conflict_priority(conflict_type):
#     """
#     Assigns priority levels to conflict types.
#     Higher priority conflicts are resolved first.
#     """
#     priority_map = {
#         "Lecturer Conflict": 3,  # Most important
#         "Room Conflict": 2,
#         "Timeslot Conflict": 1,
#         "Day Crossing": 0  # Least important
#     }
#     return priority_map.get(conflict_type, 0)  # Default priority: 0


# def find_available_consecutive_timeslots(db: Session, timetable_entry, room_id):
#     """
#     Finds a set of consecutive available timeslots for a given room.
#     Ensures that the timeslots are in the same day and do not introduce new conflicts.
#     """
#     required_timeslot_count = len(timetable_entry.timeslot_ids)

#     # Fetch all timeslots grouped by day
#     all_timeslots = db.query(TimeSlot).order_by(TimeSlot.day_index, TimeSlot.start_time).all()
#     grouped_by_day = {}

#     for ts in all_timeslots:
#         if ts.day_index not in grouped_by_day:
#             grouped_by_day[ts.day_index] = []
#         grouped_by_day[ts.day_index].append(ts)

#     # Try to find consecutive timeslots for the selected room
#     for day_index, timeslots in grouped_by_day.items():
#         for i in range(len(timeslots) - required_timeslot_count + 1):
#             selected_slots = timeslots[i:i + required_timeslot_count]
#             new_timeslot_ids = [ts.id for ts in selected_slots]

#             # Check if this move introduces new conflicts
#             if not causes_new_conflict(db, room_id, new_timeslot_ids):
#                 return new_timeslot_ids

#     return None  # No valid timeslots found


# def find_available_room(db: Session, timetable_entry):
#     """
#     Finds an available room that has sufficient capacity and is not occupied.
#     """
#     candidate_rooms = db.query(Ruangan).filter(Ruangan.kapasitas >= timetable_entry.kapasitas).all()

#     for room in candidate_rooms:
#         # Check if the room is free during all required timeslots
#         if not causes_new_conflict(db, room.id, timetable_entry.timeslot_ids):
#             return room  # Found an available room

#     return None  # No available room


# def causes_new_conflict(db: Session, room_id, timeslot_ids):
#     """
#     Checks if assigning a room and timeslot would cause new conflicts.
#     """
#     conflict = db.query(TimeTable).filter(
#         TimeTable.ruangan_id == room_id,
#         func.json_contains(TimeTable.timeslot_ids, json.dumps(timeslot_ids))
#     ).first()

#     return conflict is not None  # Returns True if conflict exists


# def generate_placeholder(db: Session, room_id, timeslot_ids):
#     """
#     Generates a placeholder string based on the new room and timeslot assignment.
#     """
#     timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()

#     if timeslots:
#         return f"1. {room_id} - {timeslots[0].day} ({timeslots[0].start_time} - {timeslots[-1].end_time})"
#     return "1. Unknown Room - Unknown Timeslot"


@router.post("/resolve-conflicts")
async def resolve_conflicts(db: Session = Depends(get_db)):
    """
    Smart conflict resolution that:
    - For each conflict, tries to find ANY new room and ANY new consecutive timeslots,
      ignoring the original room/time and ignoring any preference or day restrictions.
    - Applies the first valid combination that does not create a new conflict.
    """

    from .algorithm_routes import check_timetable_conflicts

    # Step 1: Fetch existing conflicts
    conflict_response = await check_timetable_conflicts(db)
    conflicts = conflict_response.get("conflict_details", [])
    resolved_conflicts = []

    # Sort conflicts by severity (Lecturer > Room > Timeslot > DayCrossing, etc.)
    for conflict in sorted(conflicts, key=lambda x: conflict_priority(x["type"])):
        timetable_id = conflict["timetable_id"]
        conflict_type = conflict["type"]

        # Fetch the conflicting timetable entry
        timetable_entry = db.query(TimeTable).filter(TimeTable.id == timetable_id).first()
        if not timetable_entry:
            continue

        # Attempt to find any new (room, consecutive timeslot) combination
        new_room, new_timeslot_ids = find_new_room_and_timeslot(db, timetable_entry)

        # If a valid combination is found, apply it
        if new_room and new_timeslot_ids:
            # Double-check that assigning them won't create new conflicts
            if not causes_new_conflict(db, new_room.id, new_timeslot_ids):
                # Apply the changes
                old_room_id = timetable_entry.ruangan_id
                old_timeslots = timetable_entry.timeslot_ids

                timetable_entry.ruangan_id = new_room.id
                timetable_entry.timeslot_ids = new_timeslot_ids
                timetable_entry.is_conflicted = False
                timetable_entry.reason = None  # conflict resolved

                # Generate placeholder
                new_placeholder = generate_placeholder(db, new_room.id, new_timeslot_ids)
                timetable_entry.placeholder = new_placeholder

                resolved_conflicts.append({
                    "timetable_id": timetable_entry.id,
                    "previous_room": old_room_id,
                    "new_room": new_room.id,
                    "previous_timeslot": old_timeslots,
                    "new_timeslot": new_timeslot_ids,
                    "resolved_conflict_type": conflict_type
                })
            # else: if it introduces a new conflict, skip

    db.commit()

    return {
        "message": "Conflicts resolved successfully",
        "resolved_conflicts": resolved_conflicts
    }


def conflict_priority(conflict_type):
    """
    Assigns priority levels to conflict types.
    Higher priority conflicts are resolved first.
    """
    priority_map = {
        "Lecturer Conflict": 3,  # Most important
        "Room Conflict": 2,
        "Timeslot Conflict": 1,
        "Day Crossing": 0  # Least important
    }
    return priority_map.get(conflict_type, 0)


def find_new_room_and_timeslot(db: Session, timetable_entry: TimeTable):
    """
    Tries all candidate rooms and all possible consecutive timeslots
    (any day, ignoring original timeslot) to find a valid combination.
    Returns (room, timeslot_ids) or (None, None) if no valid combination is found.
    """

    required_sks = len(timetable_entry.timeslot_ids)
    candidate_rooms = db.query(Ruangan).filter(
        Ruangan.kapasitas >= timetable_entry.kapasitas
    ).all()

    # Gather all timeslots, grouped by day
    all_timeslots = db.query(TimeSlot).order_by(TimeSlot.day_index, TimeSlot.start_time).all()
    grouped_by_day = {}
    for ts in all_timeslots:
        grouped_by_day.setdefault(ts.day_index, []).append(ts)

    # For each candidate room
    for room in candidate_rooms:
        # For each day
        for day_index, timeslots in grouped_by_day.items():
            # Slide over the timeslots to find consecutive blocks of length = required_sks
            for i in range(len(timeslots) - required_sks + 1):
                selected_block = timeslots[i : i + required_sks]

                # Ensure these timeslots are truly consecutive (IDs are sequential & same day)
                # or at least that they share the same day_index
                # (If you want strict "ID must be consecutive", you can check that too)
                if not all(ts.day_index == day_index for ts in selected_block):
                    continue

                new_timeslot_ids = [ts.id for ts in selected_block]

                # Check if there's a conflict
                if not causes_new_conflict(db, room.id, new_timeslot_ids):
                    return (room, new_timeslot_ids)

    return (None, None)


def causes_new_conflict(db: Session, room_id: int, timeslot_ids: list[int]) -> bool:
    """
    Checks if assigning a given room and a list of timeslot IDs would cause new conflicts.
    """
    # If any timetable entry in the DB uses the same room AND
    # intersects the same timeslot IDs, that's a conflict
    conflict = db.query(TimeTable).filter(
        TimeTable.ruangan_id == room_id,
        func.json_contains(TimeTable.timeslot_ids, json.dumps(timeslot_ids))
    ).first()

    return conflict is not None


def generate_placeholder(db: Session, room_id: int, timeslot_ids: list[int]) -> str:
    """
    Generates a placeholder string based on the new room and timeslot assignment.
    """
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()
    if timeslots:
        first_ts = min(timeslots, key=lambda t: t.start_time)
        last_ts = max(timeslots, key=lambda t: t.end_time)
        return f"1. Room {room_id} - {first_ts.day.value} ({first_ts.start_time} - {last_ts.end_time})"
    return "1. Unknown Room - Unknown Timeslot"

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


@router.delete("/{id}")
def delete_timetable(id: int, db: Session = Depends(get_db)):
    # Find the timetable entry
    timetable = db.query(TimeTable).filter(TimeTable.id == id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # Delete related mahasiswa_timetable entries
    db.query(MahasiswaTimeTable).filter(MahasiswaTimeTable.timetable_id == id).delete(synchronize_session=False)

    # Delete the timetable entry
    db.delete(timetable)
    db.commit()

    return {"message": "Timetable and related mahasiswa_timetable entries deleted successfully"}

