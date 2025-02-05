import string
from typing import Any, Dict, List, Optional
from numpy import number
from sqlalchemy import String, or_, text
from sqlalchemy.orm import Session
from model.matakuliah_programstudi import MataKuliahProgramStudi
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass
from model.timetable_model import TimeTable
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
    """Fetch and preprocess data."""
    start_time = time.time()
    logger.debug("Fetching data from the database...")

    courses = db.query(MataKuliah).all()
    lecturers = db.query(Dosen).all()
    rooms = db.query(Ruangan).all()
    timeslots = db.query(TimeSlot).all()
    preferences = db.query(Preference).all()
    opened_classes = db.query(OpenedClass).all()

    # Cache MataKuliah
    mata_kuliah_cache = {mk.kodemk: mk for mk in courses}

    # Cache OpenedClass
    opened_class_cache = {}
    for oc in opened_classes:
        try:
            # Ensure the relationship path exists
            if not oc.mata_kuliah_program_studi or not oc.mata_kuliah_program_studi.mata_kuliah:
                logger.warning(f"OpenedClass {oc.id} is missing MataKuliahProgramStudi or MataKuliah. Skipping.")
                continue

            # Get the associated MataKuliah
            mata_kuliah = oc.mata_kuliah_program_studi.mata_kuliah

            # Add to cache
            opened_class_cache[oc.id] = {
                "dosen_ids": [dosen.id for dosen in oc.dosens],  # Get all dosen_ids for this opened_class
                "kelas": oc.kelas,
                "sks": mata_kuliah.sks,  # Get SKS from MataKuliah
                "kapasitas": oc.kapasitas,
                "mata_kuliah": mata_kuliah,  # Store the entire MataKuliah object
            }
        except AttributeError as e:
            logger.error(f"Error processing OpenedClass {oc.id}: {e}")
            continue

    # Cache rooms and timeslots
    room_cache = {r.id: r for r in rooms}
    timeslot_cache = {t.id: t for t in timeslots}

    logger.debug(f"Fetched data in {time.time() - start_time:.2f} seconds")
    return courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache
def initialize_population(
    opened_classes, rooms, timeslots, population_size: int, opened_class_cache: Dict
) -> List[Dict]:
    """Initialize population with random schedules, ensuring consecutive timeslots for SKS and correct room types."""
    population = []
    timeslot_ids = [t.id for t in timeslots]

    for _ in range(population_size):
        timetable = []
        for opened_class in opened_classes:
            try:
                mata_kuliah = opened_class_cache[opened_class.id]["mata_kuliah"]
                sks = opened_class_cache[opened_class.id]["sks"]

                # Filter rooms based on tipe_mk
                if mata_kuliah.tipe_mk == 1:
                    valid_rooms = [room for room in rooms if room.tipe_ruangan == "T"]
                elif mata_kuliah.tipe_mk == 0:
                    valid_rooms = [room for room in rooms if room.tipe_ruangan == "P"]
                elif mata_kuliah.tipe_mk == 99:
                    valid_rooms = [room for room in rooms if room.tipe_ruangan == "S"]
                else:
                    valid_rooms = rooms  # Default to all rooms if tipe_mk is unknown

                if not valid_rooms:
                    logger.warning(f"No valid rooms found for opened class {opened_class.id} with tipe_mk {mata_kuliah.tipe_mk}")
                    continue

                room = random.choice(valid_rooms)

                # Ensure consecutive timeslots
                start_timeslot_idx = random.randint(0, len(timeslot_ids) - sks)
                assigned_timeslots = timeslot_ids[start_timeslot_idx : start_timeslot_idx + sks]

                timetable.append({
                    "opened_class_id": opened_class.id,
                    "ruangan_id": room.id,
                    "timeslot_ids": assigned_timeslots,
                    "kelas": opened_class.kelas,
                    "is_conflicted": False,
                })
            except KeyError as e:
                logger.error(f"Missing key in opened_class_cache for opened class {opened_class.id}: {e}")
                continue

        population.append(timetable)

    return population


def calculate_fitness(timetable: List[Dict], opened_class_cache: Dict, room_cache: Dict) -> int:
    """Calculate fitness score, ensuring no conflicts and proper timeslot assignments."""
    total_penalty = 0
    lecturer_timeslot_map = {}
    room_timeslot_map = {}

    # Reset conflicts for all entries
    for entry in timetable:
        entry["is_conflicted"] = False

    for entry in timetable:
        opened_class_id = entry["opened_class_id"]
        ruangan_id = entry["ruangan_id"]
        timeslot_ids = entry["timeslot_ids"]

        opened_class = opened_class_cache.get(opened_class_id)
        if not opened_class:
            logger.error(f"OpenedClass not found for ID: {opened_class_id}")
            continue

        # Fetch room and mata_kuliah from caches
        room = room_cache.get(ruangan_id)
        mata_kuliah = opened_class.get("mata_kuliah")

        # Check if room and mata_kuliah are valid
        if room and mata_kuliah:
            # Map tipe_mk to room type
            if mata_kuliah.tipe_mk == 1 and room.tipe_ruangan != "T":
                total_penalty += 20  # Penalty for theory class in non-theory room
                entry["is_conflicted"] = True
            elif mata_kuliah.tipe_mk == 0 and room.tipe_ruangan != "P":
                total_penalty += 20  # Penalty for practical class in non-practical room
                entry["is_conflicted"] = True
            elif mata_kuliah.tipe_mk == 99 and room.tipe_ruangan != "S":
                total_penalty += 20  # Penalty for special class in non-special room
                entry["is_conflicted"] = True

        # Check lecturer conflicts (overlapping timeslots for the same lecturer)
        for dosen_id in opened_class["dosen_ids"]:
            if dosen_id not in lecturer_timeslot_map:
                lecturer_timeslot_map[dosen_id] = set()
            if any(ts_id in lecturer_timeslot_map[dosen_id] for ts_id in timeslot_ids):
                total_penalty += 20
                entry["is_conflicted"] = True
            lecturer_timeslot_map[dosen_id].update(timeslot_ids)

        # Check room conflicts (overlapping timeslots for the same room)
        if ruangan_id not in room_timeslot_map:
            room_timeslot_map[ruangan_id] = set()
        if any(ts_id in room_timeslot_map[ruangan_id] for ts_id in timeslot_ids):
            total_penalty += 20
            entry["is_conflicted"] = True
        room_timeslot_map[ruangan_id].update(timeslot_ids)

        # Room type mismatch checks
        if room and mata_kuliah and room.tipe_ruangan != mata_kuliah.tipe_mk:
            total_penalty += 20
            entry["is_conflicted"] = True

    return total_penalty


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





def genetic_algorithm(db: Session, generations: int = 50, population_size: int = 50):
    clear_timetable(db)
    logger.info("Starting genetic algorithm...")

    _, _, rooms, timeslots, _, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache)

    for generation in range(generations):
        logger.info(f"Generation {generation + 1}/{generations}")
        population = evolve_population(population, opened_class_cache, room_cache, timeslots)
        best_fitness = min(calculate_fitness(timetable, opened_class_cache, room_cache) for timetable in population)
        logger.info(f"Best fitness in generation {generation + 1}: {best_fitness}")

    best_timetable = min(population, key=lambda x: calculate_fitness(x, opened_class_cache, room_cache))
    insert_timetable(db, best_timetable, opened_class_cache, room_cache, timeslot_cache)
    return best_timetable


def check_conflicts(db: Session):
    # Step 1: Reset all is_conflicted flags to False (0)
    db.query(TimeTable).update({"is_conflicted": False})
    db.commit()

    # Step 2: Query to find room conflicts
    room_conflicts_query = text("""
        SELECT 
            t1.id AS timetable_id
        FROM timetable t1
        JOIN timetable t2 
        ON t1.ruangan_id = t2.ruangan_id 
        AND t1.timeslot_ids = t2.timeslot_ids 
        AND t1.id != t2.id;
    """)

    # Step 3: Query to find lecturer conflicts
    lecturer_conflicts_query = text("""
        SELECT 
            t1.id AS timetable_id
        FROM timetable t1
        JOIN opened_class oc1 ON t1.opened_class_id = oc1.id
        JOIN openedclass_dosen od1 ON oc1.id = od1.opened_class_id
        JOIN timetable t2 ON t2.opened_class_id = oc1.id
        JOIN openedclass_dosen od2 ON oc1.id = od2.opened_class_id
        WHERE t1.timeslot_ids = t2.timeslot_ids 
        AND t1.id != t2.id
        AND od1.dosen_id = od2.dosen_id;
    """)

    # Step 4: Query to find overlapping timeslots
    overlapping_timeslots_query = text("""
        SELECT 
            t1.id AS timetable_id
        FROM timetable t1
        JOIN timetable t2 
        ON t1.opened_class_id = t2.opened_class_id 
        AND t1.timeslot_ids && t2.timeslot_ids 
        AND t1.id != t2.id;
    """)

    # Step 5: Execute queries and get conflicting timetable IDs
    room_conflicts = [row.timetable_id for row in db.execute(room_conflicts_query).fetchall()]
    lecturer_conflicts = [row.timetable_id for row in db.execute(lecturer_conflicts_query).fetchall()]
    overlapping_timeslots = [row.timetable_id for row in db.execute(overlapping_timeslots_query).fetchall()]

    # Step 6: Combine all conflicting IDs
    conflicting_ids = set(room_conflicts + lecturer_conflicts + overlapping_timeslots)

    # Step 7: Update the is_conflicted column for conflicting rows
    for timetable_id in conflicting_ids:
        db.query(TimeTable).filter(TimeTable.id == timetable_id).update({"is_conflicted": True})

    # Step 8: Commit changes to the database
    db.commit()

    return {
        "room_conflicts": room_conflicts,
        "lecturer_conflicts": lecturer_conflicts,
        "overlapping_timeslots": overlapping_timeslots,
    }
def simulated_annealing(
    db: Session,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100
):
    """Simulated Annealing algorithm for scheduling."""
    clear_timetable(db)
    logger.info("Starting Simulated Annealing for scheduling...")
    
    # Fetch required data
    _, _, rooms, timeslots, _, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    
    # Generate initial random solution
    current_solution = initialize_population(opened_classes, rooms, timeslots, 1, opened_class_cache)[0]
    current_fitness = calculate_fitness(current_solution, opened_class_cache, room_cache)
    best_solution = current_solution
    best_fitness = current_fitness
    temperature = initial_temperature
    
    logger.debug(f"Initial Solution Fitness: {current_fitness}")
    
    while temperature > 1:
        logger.debug(f"Current Temperature: {temperature:.2f}")
        
        for i in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache)
            new_fitness = calculate_fitness(new_solution, opened_class_cache, room_cache)
            
            logger.debug(f"Iteration {i + 1}: New Fitness = {new_fitness}, Current Fitness = {current_fitness}")
            
            # Calculate acceptance probability
            if new_fitness < current_fitness:
                acceptance_probability = 1.0  # Always accept better solution
                logger.debug("New solution is better. Accepting it.")
            else:
                acceptance_probability = math.exp((current_fitness - new_fitness) / temperature)
                logger.debug(f"Acceptance Probability: {acceptance_probability}")
            
            if random.random() < acceptance_probability:
                current_solution = new_solution
                current_fitness = new_fitness
                logger.debug("Accepted new solution.")
                
                if current_fitness < best_fitness:
                    best_solution = current_solution
                    best_fitness = current_fitness
                    logger.debug(f"New Best Fitness: {best_fitness}")
        
        temperature *= cooling_rate  # Cool down the temperature
        logger.info(f"Temperature: {temperature:.2f}, Best Fitness: {best_fitness}")
    
    insert_timetable(db, best_solution, opened_class_cache, room_cache, timeslot_cache)
    logger.info("Simulated Annealing completed. Best Fitness: %s", best_fitness)
    return best_solution


def generate_neighbor_solution(
    current_solution: List[Dict], opened_classes, rooms, timeslots, opened_class_cache: Dict
) -> List[Dict]:
    """Generate a new neighboring solution by modifying a random assignment."""
    new_solution = current_solution.copy()
    entry = random.choice(new_solution)  # Select a random timetable entry
    
    # Get new random timeslot and room
    timeslot_ids = [t.id for t in timeslots]
    new_start_timeslot_idx = random.randint(0, len(timeslot_ids) - len(entry["timeslot_ids"]))
    new_entry = entry.copy()
    new_entry["timeslot_ids"] = timeslot_ids[new_start_timeslot_idx : new_start_timeslot_idx + len(entry["timeslot_ids"])]
    new_entry["ruangan_id"] = random.choice(rooms).id  # Assign a new random room
    
    # Replace the entry in the new solution
    new_solution.remove(entry)
    new_solution.append(new_entry)
    logger.debug(f"Generated Neighbor Solution: {new_entry}")
    return new_solution


def clear_timetable(db: Session):
    """Deletes all entries in the timetable table."""
    db.query(TimeTable).delete()
    db.commit()


from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db

router = APIRouter()



# FastAPI route for SA scheduling
router = APIRouter()

@router.post("/generate-schedule-sa")
async def generate_schedule_sa(db: Session = Depends(get_db)):
    try:
        logger.info("Generating schedule using Simulated Annealing...")
        best_timetable = simulated_annealing(db)
        return {"message": "Schedule generated successfully using Simulated Annealing", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-schedule")
async def generate_schedule(db: Session = Depends(get_db)):
    try:
        best_timetable = genetic_algorithm(db)
        return {"message": "Schedule generated successfully", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
            "code": timetable.opened_class.mata_kuliah_program_studi.mata_kuliah.kodemk,
            "name": timetable.opened_class.mata_kuliah_program_studi.mata_kuliah.namamk  # Fixed this line
        },
        "class": timetable.kelas,
        "room": {
            "id": timetable.ruangan.id,
            "code": timetable.ruangan.kode_ruangan,
            "name": timetable.ruangan.nama_ruang,
            "capacity": timetable.ruangan.kapasitas
        },
        "lecturers": [
            {
                "id": dosen.id,
                "name": dosen.nama
            }
            for dosen in timetable.opened_class.dosens
        ],
        "capacity": timetable.kapasitas,
        "enrolled": timetable.kuota,
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

@router.get("/formatted-timetable")
async def get_timetable(
    academic_period_id: int,
    db: Session = Depends(get_db)
):
    timetables = (
        db.query(TimeTable)
        .join(TimeTable.opened_class)
        .join(TimeTable.ruangan)
        .join(OpenedClass.mata_kuliah_program_studi)
        .join(MataKuliahProgramStudi.mata_kuliah)
        .join(OpenedClass.dosens)
        .filter(TimeTable.academic_period_id == academic_period_id)
        .all()
    )
    
    return [format_timetable(t) for t in timetables]
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
            ).label("dosen_names")  # ✅ Properly formatted dosen names
        ).join(OpenedClass, TimeTable.opened_class_id == OpenedClass.id) \
         .join(MataKuliah, OpenedClass.mata_kuliah_program_studi.has(mata_kuliah_id=MataKuliah.kodemk)) \
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



@router.get("/check-conflicts")
async def check_timetable_conflicts(db: Session = Depends(get_db)):
    conflicts = check_conflicts(db)
    return {"conflicts": conflicts}
