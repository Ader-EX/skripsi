from typing import Dict, List
from sqlalchemy.orm import Session
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass
from model.pengajaran_model import Pengajaran
from model.timetable_model import TimeTable
import random
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def clear_timetable(db: Session):
    """
    Deletes all entries in the timetable table.
    """
    logger.debug("Clearing all entries in the timetable table...")
    try:
        db.query(TimeTable).delete()  # Delete all rows in the timetable table
        db.commit()
        logger.debug("Timetable cleared successfully.")
    except Exception as e:
        db.rollback()  # Rollback in case of an error
        logger.error(f"Error clearing timetable: {e}")
        raise

def format_placeholder(entry: Dict, pengajaran_cache: Dict, timeslot_cache: Dict) -> str:
    """
    Generates a placeholder string for a timetable entry.
    """
    pengajaran = pengajaran_cache.get(entry["pengajaran_id"])
    if pengajaran is None:
        logger.error(f"Pengajaran not found for ID: {entry['pengajaran_id']}")
        return ""

    timeslot = timeslot_cache.get(entry["timeslot_id"])
    if timeslot is None:
        logger.error(f"Timeslot not found for ID: {entry['timeslot_id']}")
        return ""

    # Extract relevant details
    course_name = pengajaran["opened_class"].mata_kuliah_program_studi.mata_kuliah.namamk
    kelas = entry["kelas"]
    day = timeslot.day
    start_time = timeslot.start_time
    end_time = timeslot.end_time

    # Format the placeholder string
    placeholder = (
        f"1. {day}, ({start_time}-{end_time}) {course_name} {kelas}"
    )

    # Add additional information if needed
    if pengajaran["opened_class"].mata_kuliah_program_studi.mata_kuliah.have_kelas_besar:
        placeholder += f"\n2. {day}, ({start_time}-{end_time}) VCR-FIK-KB"

    return placeholder

# Fetch Data and Cache
def fetch_data(db: Session):
    start_time = time.time()
    logger.debug("Fetching data from the database...")

    # Fetch data
    courses = db.query(MataKuliah).all()
    lecturers = db.query(Dosen).all()
    rooms = db.query(Ruangan).all()
    timeslots = db.query(TimeSlot).all()
    preferences = db.query(Preference).all()
    opened_classes = db.query(OpenedClass).all()
    pengajaran_list = db.query(Pengajaran).all()

    # Cache MataKuliah and Pengajaran
    mata_kuliah_cache = {mk.kodemk: mk for mk in courses}
    pengajaran_cache = {
        p.id: {
            "dosen_id": p.dosen_id,
            "opened_class": p.opened_class,
            "sks": mata_kuliah_cache[p.opened_class.mata_kuliah_program_studi.mata_kuliah.kodemk].sks
        }
        for p in pengajaran_list
    }
    room_cache = {r.id: r for r in rooms}
    timeslot_cache = {t.id: t for t in timeslots}

    logger.debug(f"Fetched data in {time.time() - start_time:.2f} seconds")
    return courses, lecturers, rooms, timeslots, preferences, opened_classes, pengajaran_list, pengajaran_cache, room_cache, timeslot_cache

def initialize_population(pengajaran_list, rooms, timeslots, population_size: int, pengajaran_cache: Dict) -> List[Dict]:
    start_time = time.time()
    logger.debug(f"Initializing population of size {population_size}...")

    population = []
    for i in range(population_size):
        timetable = []
        for pengajaran in pengajaran_list:
            room = random.choice(rooms)
            sks = pengajaran_cache[pengajaran.id]["sks"]  # Get SKS for the course

            # Find consecutive timeslots
            for _ in range(sks):
                timeslot = random.choice(timeslots)
                timetable.append({
                    "pengajaran_id": pengajaran.id,
                    "ruangan_id": room.id,
                    "timeslot_id": timeslot.id,  # Single timeslot ID
                    "kelas": pengajaran.opened_class.kelas,
                    "is_conflicted": False  # Initialize is_conflicted to False
                })
                logger.debug(f"Assigned timeslot {timeslot.id} to pengajaran {pengajaran.id} in room {room.id}")
        population.append(timetable)
        logger.debug(f"Generated timetable {i + 1} with {len(timetable)} entries.")
    
    logger.debug(f"Population initialized in {time.time() - start_time:.2f} seconds")
    return population

def calculate_fitness(timetable: List[Dict], pengajaran_cache: Dict, room_cache: Dict) -> int:
    total_penalty = 0
    lecturer_timeslots = {}  # Tracks timeslots assigned to each lecturer
    room_timeslot_assignments = {}  # Tracks room and timeslot combinations

    for entry in timetable:
        pengajaran_id = entry["pengajaran_id"]
        ruangan_id = entry["ruangan_id"]
        timeslot_id = entry["timeslot_id"]

        pengajaran = pengajaran_cache.get(pengajaran_id)
        if pengajaran is None:
            logger.error(f"Pengajaran not found for ID: {pengajaran_id}")
            continue

        lecturer_id = pengajaran["dosen_id"]

        # Check lecturer conflicts
        if lecturer_id in lecturer_timeslots:
            if timeslot_id in lecturer_timeslots[lecturer_id]:
                logger.debug(f"Lecturer conflict detected for lecturer {lecturer_id} in timeslot {timeslot_id}")
                total_penalty += 20  # Lecturer conflict penalty
                entry["is_conflicted"] = True  # Mark as conflicted
            else:
                lecturer_timeslots[lecturer_id].add(timeslot_id)
        else:
            lecturer_timeslots[lecturer_id] = {timeslot_id}

        # Check room and timeslot conflicts
        room_timeslot_key = (ruangan_id, timeslot_id)
        if room_timeslot_key in room_timeslot_assignments:
            logger.debug(f"Room and timeslot conflict detected for room {ruangan_id} in timeslot {timeslot_id}")
            total_penalty += 20  # Room and timeslot conflict penalty
            entry["is_conflicted"] = True  # Mark as conflicted
        else:
            room_timeslot_assignments[room_timeslot_key] = True

        # Room type mismatch checks
        room = room_cache.get(ruangan_id)
        mata_kuliah = pengajaran["opened_class"].mata_kuliah_program_studi.mata_kuliah
        if room is None or mata_kuliah is None:
            logger.error(f"Room or MataKuliah not found for room ID: {ruangan_id} or mata_kuliah ID: {mata_kuliah.kodemk}")
            continue

        if room.tipe_ruangan != mata_kuliah.tipe_mk:
            logger.debug(f"Room type mismatch for room {ruangan_id} (type: {room.tipe_ruangan}) and course {pengajaran_id} (type: {mata_kuliah.tipe_mk})")
            total_penalty += 20  # Room type mismatch penalty
            entry["is_conflicted"] = True  # Mark as conflicted

    return total_penalty

# Evolution Process
def evolve_population(population: List[List[Dict]], pengajaran_cache: Dict, room_cache: Dict, timeslots: List[TimeSlot]) -> List[List[Dict]]:
    logger.debug("Evolving population...")

    # Sequential fitness calculation
    fitness_scores = [calculate_fitness(timetable, pengajaran_cache, room_cache) for timetable in population]

    probabilities = [1 / score for score in fitness_scores]

    # Select parents and crossover
    new_population = []
    for _ in range(len(population)):
        parent1, parent2 = random.choices(population, weights=probabilities, k=2)
        child = parent1[:len(parent1)//2] + parent2[len(parent2)//2:]
        new_population.append(child)

    # Mutation
    for timetable in new_population:
        if random.random() < 0.1:  # Mutation rate
            gene_to_mutate = random.randint(0, len(timetable) - 1)
            timetable[gene_to_mutate]["timeslot_id"] = random.choice(timeslots).id

    return new_population

def insert_timetable(db: Session, timetable: List[Dict], pengajaran_cache: Dict, room_cache: Dict, timeslot_cache: Dict):
    logger.debug("Inserting best timetable into the database...")
    for entry in timetable:
        pengajaran = pengajaran_cache.get(entry["pengajaran_id"])
        if pengajaran is None:
            logger.error(f"Pengajaran not found for ID: {entry['pengajaran_id']}")
            continue

        room = room_cache.get(entry["ruangan_id"])
        if room is None:
            logger.error(f"Room not found for ID: {entry['ruangan_id']}")
            continue

        timeslot = timeslot_cache.get(entry["timeslot_id"])
        if timeslot is None:
            logger.error(f"Timeslot not found for ID: {entry['timeslot_id']}")
            continue

        timetable_entry = TimeTable(
            pengajaran_id=entry["pengajaran_id"],
            ruangan_id=entry["ruangan_id"],
            timeslot_ids=[entry["timeslot_id"]],  # Pass as a list
            is_conflicted=entry.get("is_conflicted", False),
            kelas=entry["kelas"],
            kapasitas=pengajaran["opened_class"].kapasitas,
            kuota=0,
            academic_period_id=1,
            placeholder=format_placeholder(entry, pengajaran_cache, timeslot_cache)
        )
        db.add(timetable_entry)
    db.commit()
    logger.debug("Timetable inserted successfully.")

def get_timeslots_for_timetable(db: Session, timetable_entry: TimeTable) -> List[TimeSlot]:
    timeslot_ids = timetable_entry.timeslot_ids  # Get the list of timeslot IDs
    timeslots = db.query(TimeSlot).filter(TimeSlot.id.in_(timeslot_ids)).all()  # Fetch the timeslots
    return timeslots

# Genetic Algorithm
def genetic_algorithm(db: Session, generations: int = 50, population_size: int = 50):
    start_time = time.time()
    clear_timetable(db)

    logger.info("Starting genetic algorithm...")

    # Fetch data
    courses, lecturers, rooms, timeslots, preferences, opened_classes, pengajaran_list, pengajaran_cache, room_cache, timeslot_cache = fetch_data(db)
    population = initialize_population(pengajaran_list, rooms, timeslots, population_size, pengajaran_cache)

    for generation in range(generations):
        logger.info(f"Generation {generation + 1}/{generations}")
        population = evolve_population(population, pengajaran_cache, room_cache, timeslots)
        best_fitness = min(calculate_fitness(timetable, pengajaran_cache, room_cache) for timetable in population)
        logger.info(f"Best fitness in generation {generation + 1}: {best_fitness}")

    best_timetable = min(population, key=lambda x: calculate_fitness(x, pengajaran_cache, room_cache))
    logger.info(f"Genetic algorithm completed in {time.time() - start_time:.2f} seconds")

    insert_timetable(db, best_timetable, pengajaran_cache, room_cache, timeslot_cache)
    return best_timetable

# FastAPI Route
from fastapi import APIRouter, Depends, HTTPException
from database import get_db

router = APIRouter()

@router.post("/generate-schedule")
async def generate_schedule(db: Session = Depends(get_db)):
    try:
        logger.info("Generating schedule...")
        best_timetable = genetic_algorithm(db)
        return {"message": "Schedule generated successfully", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.delete("/reset-schedule")
async def reset_schedule(db: Session = Depends(get_db)):
    try:
        logger.info("Resetting schedule...")
        clear_timetable(db)
        return {"message": "Schedule reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))