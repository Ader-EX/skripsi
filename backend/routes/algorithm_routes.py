import string
from typing import Any, Dict, List, Optional
from numpy import number
from sqlalchemy import String, or_, text
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

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache):
    """
    Initialize valid schedules by ensuring "Senin" is included and classes have proper timeslot sequences.
    """
    population = []
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))

    for _ in range(population_size):
        solution = []
        room_schedule = {}
        lecturer_schedule = {}

        sorted_classes = sorted(
            opened_classes, key=lambda oc: opened_class_cache[oc.id]["sks"], reverse=True
        )

        for oc in sorted_classes:
            try:
                class_info = opened_class_cache[oc.id]
                sks = class_info["sks"]

                compatible_rooms = [r for r in rooms if r.tipe_ruangan == class_info["mata_kuliah"].tipe_mk]
                if not compatible_rooms:
                    continue

                assigned = False
                random.shuffle(compatible_rooms)

                for room in compatible_rooms:
                    if assigned:
                        break

                    for start_idx in range(len(timeslots_list) - sks + 1):
                        slots = timeslots_list[start_idx : start_idx + sks]

                        if not all(slots[i].day_index == slots[0].day_index and slots[i].id == slots[i - 1].id + 1 for i in range(1, sks)):
                            continue

                        slot_available = True
                        for slot in slots:
                            if (room.id, slot.id) in room_schedule:
                                slot_available = False
                                break
                            for dosen_id in class_info["dosen_ids"]:
                                if (dosen_id, slot.id) in lecturer_schedule:
                                    slot_available = False
                                    break

                        if slot_available:
                            for slot in slots:
                                room_schedule[(room.id, slot.id)] = oc.id
                                for dosen_id in class_info["dosen_ids"]:
                                    lecturer_schedule[(dosen_id, slot.id)] = oc.id

                            solution.append((oc.id, room.id, slots[0].id))
                            assigned = True
                            break

                if not assigned:
                    logger.warning(f"Could not assign class {oc.id} in initial population")

            except Exception as e:
                logger.error(f"Error initializing class {oc.id}: {e}")
                continue

        population.append(solution)

    return population




# def calculate_fitness(timetable: List[Dict], opened_class_cache: Dict, room_cache: Dict) -> int:
#     """Calculate fitness score, ensuring no conflicts and proper timeslot assignments."""
#     total_penalty = 0
#     lecturer_timeslot_map = {}
#     room_timeslot_map = {}

#     # Reset conflicts for all entries
#     for entry in timetable:
#         entry["is_conflicted"] = False

#     for entry in timetable:
#         opened_class_id = entry["opened_class_id"]
#         ruangan_id = entry["ruangan_id"]
#         timeslot_ids = entry["timeslot_ids"]

#         opened_class = opened_class_cache.get(opened_class_id)
#         if not opened_class:
#             logger.error(f"OpenedClass not found for ID: {opened_class_id}")
#             continue

#         # Fetch room and mata_kuliah from caches
#         room = room_cache.get(ruangan_id)
#         mata_kuliah = opened_class.get("mata_kuliah")

#         # Check if room and mata_kuliah are valid
#         if room and mata_kuliah:
#             # Map tipe_mk to room type
#             if mata_kuliah.tipe_mk == 1 and room.tipe_ruangan != "T":
#                 total_penalty += 20  # Penalty for theory class in non-theory room
#                 entry["is_conflicted"] = True
#             elif mata_kuliah.tipe_mk == 0 and room.tipe_ruangan != "P":
#                 total_penalty += 20  # Penalty for practical class in non-practical room
#                 entry["is_conflicted"] = True
#             elif mata_kuliah.tipe_mk == 99 and room.tipe_ruangan != "S":
#                 total_penalty += 20  # Penalty for special class in non-special room
#                 entry["is_conflicted"] = True

#         # Check lecturer conflicts (overlapping timeslots for the same lecturer)
#         for dosen_id in opened_class["dosen_ids"]:
#             if dosen_id not in lecturer_timeslot_map:
#                 lecturer_timeslot_map[dosen_id] = set()
#             if any(ts_id in lecturer_timeslot_map[dosen_id] for ts_id in timeslot_ids):
#                 total_penalty += 20
#                 entry["is_conflicted"] = True
#             lecturer_timeslot_map[dosen_id].update(timeslot_ids)

#         # Check room conflicts (overlapping timeslots for the same room)
#         if ruangan_id not in room_timeslot_map:
#             room_timeslot_map[ruangan_id] = set()
#         if any(ts_id in room_timeslot_map[ruangan_id] for ts_id in timeslot_ids):
#             total_penalty += 20
#             entry["is_conflicted"] = True
#         room_timeslot_map[ruangan_id].update(timeslot_ids)

#         # Room type mismatch checks
#         if room and mata_kuliah and room.tipe_ruangan != mata_kuliah.tipe_mk:
#             total_penalty += 20
#             entry["is_conflicted"] = True

#     return total_penalty


def evolve_population(
    population: List[List[Dict]], opened_class_cache: Dict, room_cache: Dict, timeslots: List[TimeSlot]
) -> List[List[Dict]]:
    """Evolve the population with crossover and mutation."""
    fitness_scores = [calculate_fitness(timetable, opened_class_cache, room_cache) for timetable in population]
    probabilities = [1 / (score + 1) for score in fitness_scores]

    new_population = []
    for _ in range(len(population)):
        parent1, parent2 = random.choices(population, weights=probabilities, k=2)
        child = parent1[:len(parent1) // 2] + parent2[len(parent2) // 2:]
        new_population.append(child)

    # Mutation
    for timetable in new_population:
        if random.random() < 0.1:
            gene = random.choice(timetable)
            start_timeslot_idx = random.randint(0, len(timeslots) - len(gene["timeslot_ids"]))
            gene["timeslot_ids"] = [timeslots[i].id for i in range(start_timeslot_idx, start_timeslot_idx + len(gene["timeslot_ids"]))]

    return new_population

def insert_timetable(db: Session, timetable: List[Dict], opened_class_cache: Dict, room_cache: Dict, timeslot_cache: Dict):
    """Insert the best timetable into the database, generating the placeholder dynamically."""
    for entry in timetable:
        try:
            opened_class = opened_class_cache[entry["opened_class_id"]]
            mata_kuliah = opened_class["mata_kuliah"]
            room = room_cache[entry["ruangan_id"]]
            timeslot_ids = entry["timeslot_ids"]

            # Get the first timeslot for the class
            first_timeslot = timeslot_cache[timeslot_ids[0]]
            day = first_timeslot.day  # Assuming `day` is the day field in TimeSlot
            start_time = first_timeslot.start_time  # Assuming `start_time` is the start time field
            end_time = timeslot_cache[timeslot_ids[-1]].end_time  # Assuming `end_time` is the end time field

            # Generate the placeholder for the designated time
            placeholder = f"1. {room.kode_ruangan} - {day} ({start_time} - {end_time})"

            # If it's a kelas besar, add the second entry
            if mata_kuliah.have_kelas_besar:
                placeholder += f"\n2. FIK-VCR-KB - {day} ({start_time} - {end_time})"

            # Create the TimeTable entry
            timetable_entry = TimeTable(
                opened_class_id=entry["opened_class_id"],
                ruangan_id=entry["ruangan_id"],
                timeslot_ids=entry["timeslot_ids"],
                is_conflicted=entry["is_conflicted"],
                kelas=entry["kelas"],
                kapasitas=opened_class["kapasitas"],
                academic_period_id=1,
                placeholder=placeholder,  # Add the dynamically generated placeholder
            )
            db.add(timetable_entry)
        except KeyError as e:
            logger.error(f"Missing key in opened_class_cache or room_cache for timetable entry: {e}")
            continue

    db.commit()
    logger.debug("Timetable inserted successfully.")





# def genetic_algorithm(db: Session, generations: int = 50, population_size: int = 50):
#     clear_timetable(db)
#     logger.info("Starting genetic algorithm...")

#     _, _, rooms, timeslots, _, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
#     population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache)

#     for generation in range(generations):
#         logger.info(f"Generation {generation + 1}/{generations}")
#         population = evolve_population(population, opened_class_cache, room_cache, timeslots)
#         best_fitness = min(calculate_fitness(timetable, opened_class_cache, room_cache) for timetable in population)
#         logger.info(f"Best fitness in generation {generation + 1}: {best_fitness}")

#     best_timetable = min(population, key=lambda x: calculate_fitness(x, opened_class_cache, room_cache))
#     insert_timetable(db, best_timetable, opened_class_cache, room_cache, timeslot_cache)
#     return best_timetable


# def check_conflicts(db: Session):
#     # Step 1: Reset all is_conflicted flags to False (0)
#     db.query(TimeTable).update({"is_conflicted": False})
#     db.commit()

#     # Step 2: Query to find room conflicts
#     room_conflicts_query = text("""
#         SELECT 
#             t1.id AS timetable_id
#         FROM timetable t1
#         JOIN timetable t2 
#         ON t1.ruangan_id = t2.ruangan_id 
#         AND t1.timeslot_ids = t2.timeslot_ids 
#         AND t1.id != t2.id;
#     """)

#     # Step 3: Query to find lecturer conflicts
#     lecturer_conflicts_query = text("""
#         SELECT 
#             t1.id AS timetable_id
#         FROM timetable t1
#         JOIN opened_class oc1 ON t1.opened_class_id = oc1.id
#         JOIN openedclass_dosen od1 ON oc1.id = od1.opened_class_id
#         JOIN timetable t2 ON t2.opened_class_id = oc1.id
#         JOIN openedclass_dosen od2 ON oc1.id = od2.opened_class_id
#         WHERE t1.timeslot_ids = t2.timeslot_ids 
#         AND t1.id != t2.id
#         AND od1.dosen_id = od2.dosen_id;
#     """)

#     # Step 4: Query to find overlapping timeslots
#     overlapping_timeslots_query = text("""
#         SELECT 
#             t1.id AS timetable_id
#         FROM timetable t1
#         JOIN timetable t2 
#         ON t1.opened_class_id = t2.opened_class_id 
#         AND t1.timeslot_ids && t2.timeslot_ids 
#         AND t1.id != t2.id;
#     """)

#     # Step 5: Execute queries and get conflicting timetable IDs
#     room_conflicts = [row.timetable_id for row in db.execute(room_conflicts_query).fetchall()]
#     lecturer_conflicts = [row.timetable_id for row in db.execute(lecturer_conflicts_query).fetchall()]
#     overlapping_timeslots = [row.timetable_id for row in db.execute(overlapping_timeslots_query).fetchall()]

#     # Step 6: Combine all conflicting IDs
#     conflicting_ids = set(room_conflicts + lecturer_conflicts + overlapping_timeslots)

#     # Step 7: Update the is_conflicted column for conflicting rows
#     for timetable_id in conflicting_ids:
#         db.query(TimeTable).filter(TimeTable.id == timetable_id).update({"is_conflicted": True})

#     # Step 8: Commit changes to the database
#     db.commit()

#     return {
#         "room_conflicts": room_conflicts,
#         "lecturer_conflicts": lecturer_conflicts,
#         "overlapping_timeslots": overlapping_timeslots,
#     }





def clear_timetable(db: Session):
    """Deletes all entries in the timetable table."""
    db.execute(text("DELETE FROM mahasiswa_timetable"))
    db.execute(text("DELETE FROM timetable"))
    db.commit()


from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db

router = APIRouter()



# @router.post("/generate-schedule")
# async def generate_schedule(db: Session = Depends(get_db)):
#     try:
#         best_timetable = genetic_algorithm(db)
#         return {"message": "Schedule generated successfully", "timetable": best_timetable}
#     except Exception as e:
#         logger.error(f"Error generating schedule: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset-schedule")
async def reset_schedule(db: Session = Depends(get_db)):
    try:
        clear_timetable(db)
        return {"message": "Schedule reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

router = APIRouter()

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

@router.get("/formatted-timetable")
async def get_timetable(
    db: Session = Depends(get_db),
    is_conflicted: Optional[bool] = Query(None, description="Filter by conflict status"),
    page: int = Query(1, description="Page number"),
    limit: int = Query(10, description="Number of items per page"),
    filterText: Optional[str] = Query(None, description="Filter by subject or lecturer")
):
    try:
        query = db.query(TimeTable).options(
            joinedload(TimeTable.opened_class)
            .joinedload(OpenedClass.mata_kuliah),
            joinedload(TimeTable.ruangan),
            joinedload(TimeTable.opened_class)
            .joinedload(OpenedClass.dosens),
        )

        # Apply conflict filter if specified
        if is_conflicted is not None:
            query = query.filter(TimeTable.is_conflicted == is_conflicted)

        # Apply search filter if specified
        if filterText:
            search_term = f"%{filterText}%"
            query = query.join(OpenedClass).join(MataKuliah).join(OpenedClass.dosens).filter(
                or_(
                    MataKuliah.namamk.ilike(search_term),
                    MataKuliah.kodemk.ilike(search_term),
                    Dosen.nama.ilike(search_term)
                )
            ).distinct()

        # Order by `is_conflicted=True` first
        query = query.order_by(desc(TimeTable.is_conflicted))

        # Count total records before pagination
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
                    "name": mata_kuliah.namamk
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
            })

        return {
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
    search: Optional[str] = Query(None, description="Search by course name or code")
):
    # ✅ Get Active Academic Period
    active_academic_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_academic_period:
        raise HTTPException(status_code=404, detail="No active academic period found")

    # ✅ Base Query for Timetables
    timetables_query = (
        db.query(TimeTable)
        .join(TimeTable.opened_class)
        .join(OpenedClass.mata_kuliah)
        .join(TimeTable.ruangan)
        .join(OpenedClass.dosens)
        .join(Dosen.user)
        .filter(TimeTable.academic_period_id == active_academic_period.id)
    )

    # ✅ Apply Search Filter if provided
    if search:
        search_term = f"%{search}%"
        timetables_query = timetables_query.filter(
            or_(
                MataKuliah.namamk.ilike(search_term),
                MataKuliah.kodemk.ilike(search_term)
            )
        )

    # ✅ Execute Query
    timetables = timetables_query.all()

    # ✅ Get All Time Slots
    time_slots = db.query(TimeSlot).all()

    # ✅ Get All Rooms
    rooms = db.query(Ruangan).all()

    # ✅ Construct Metadata
    metadata = {
        "semester": f"{active_academic_period.tahun_ajaran} - Semester {active_academic_period.semester}",
        "week_start": f"{active_academic_period.start_date}",
        "week_end": f"{active_academic_period.end_date}"
    }

    # ✅ Construct Time Slots Data
    time_slots_data = [
        {
            "id": ts.id,
            "day": ts.day.value,
            "start_time": ts.start_time.strftime("%H:%M"),
            "end_time": ts.end_time.strftime("%H:%M")
        }
        for ts in time_slots
    ]

    # ✅ Construct Rooms Data
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

    # ✅ Construct Schedules Data with Conflict Information
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
                    "day": ts.day,
                    "start_time": ts.start_time.strftime("%H:%M"),
                    "end_time": ts.end_time.strftime("%H:%M")
                }
                for ts in timetable.timeslots
            ],
            "student_count": timetable.kuota,
            "max_capacity": timetable.opened_class.kapasitas,
            "academic_year": active_academic_period.tahun_ajaran,
            "semester_period": active_academic_period.semester,
            # Add conflict information
            "is_conflicted": timetable.is_conflicted,
            "conflict_details": timetable.conflict_details if timetable.is_conflicted else None
        }
        for timetable in timetables
    ]

    # ✅ Construct Filters
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

    # ✅ Final Response
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

def check_conflicts(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    """
    Detailed conflict checking for timetable assignments.
    
    Returns:
    - Total number of conflicts
    - Detailed conflict information
    - Whether all conflicts are resolved
    """
    conflicts = 0
    conflict_details = []
    timeslot_usage = {}  # {timeslot_id: [(room_id, opened_class_id, timetable_id)]}
    lecturer_schedule = {}  # {(dosen_id, timeslot_id): (opened_class_id, timetable_id)}

    for assignment in solution:
        opened_class_id, room_id, timeslot_id = assignment

        # Find the corresponding timetable entry
        timetable_entry = db.query(TimeTable).filter(
            TimeTable.opened_class_id == opened_class_id, 
            TimeTable.timeslot_ids[0] == timeslot_id
        ).first()

        if not timetable_entry:
            continue  # Skip if no matching timetable entry

        class_info = opened_class_cache[opened_class_id]
        sks = class_info['sks']
        current_timeslot = timeslot_cache[timeslot_id]

        for i in range(sks):
            current_id = timeslot_id + i

            # Invalid timeslot check
            if current_id not in timeslot_cache:
                conflict_details.append({
                    'type': 'Invalid Timeslot',
                    'timetable_id': timetable_entry.id,
                    'opened_class_id': opened_class_id,
                    'reason': f'Timeslot {current_id} does not exist in timeslot cache',
                    'severity': 'High'
                })
                conflicts += 1000
                continue

            # Day crossing check
            next_timeslot = timeslot_cache[current_id]
            if next_timeslot.day != current_timeslot.day:
                conflict_details.append({
                    'type': 'Day Crossing',
                    'timetable_id': timetable_entry.id,
                    'opened_class_id': opened_class_id,
                    'reason': f'Class spans multiple days (from {current_timeslot.day} to {next_timeslot.day})',
                    'severity': 'High'
                })
                conflicts += 1000
                continue

            # Room conflicts check
            if current_id not in timeslot_usage:
                timeslot_usage[current_id] = []

            for used_room, used_class_id, used_timetable_id in timeslot_usage[current_id]:
                if used_room == room_id:
                    conflict_details.append({
                        'type': 'Room Conflict',
                        'timetable_id': timetable_entry.id,
                        'conflicting_timetable_id': used_timetable_id,
                        'opened_class_id': opened_class_id,
                        'conflicting_opened_class_id': used_class_id,
                        'room_id': room_id,
                        'timeslot_id': current_id,
                        'reason': f'Room {room_id} is already in use at timeslot {current_id}'
                    })
                    conflicts += 1

            timeslot_usage[current_id].append((room_id, opened_class_id, timetable_entry.id))

            # Lecturer conflicts check
            for dosen_id in class_info['dosen_ids']:
                schedule_key = (dosen_id, current_id)

                if schedule_key in lecturer_schedule:
                    conflict_details.append({
                        'type': 'Lecturer Conflict',
                        'timetable_id': timetable_entry.id,
                        'conflicting_timetable_id': lecturer_schedule[schedule_key][1],
                        'opened_class_id': opened_class_id,
                        'conflicting_opened_class_id': lecturer_schedule[schedule_key][0],
                        'dosen_id': dosen_id,
                        'timeslot_id': current_id,
                        'reason': f'Dosen {dosen_id} telah mengajar kelas lain di timeslot {current_id}'
                    })
                    conflicts += 1

                lecturer_schedule[schedule_key] = (opened_class_id, timetable_entry.id)

    # If no conflicts, set all `is_conflicted = 0`
    if conflicts == 0:
        db.query(TimeTable).update({"is_conflicted": False}, synchronize_session=False)
    else:
        db.query(TimeTable).update({"is_conflicted": True}, synchronize_session=False)

    db.commit()

    return {
        'total_conflicts': conflicts,
        'conflict_details': conflict_details
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
