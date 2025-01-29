from typing import Dict, List
from sqlalchemy.orm import Session
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass
# from model.pengajaran_model import Pengajaran
from model.timetable_model import TimeTable
import random
import logging
import time

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)


# ### Helper Functions ###
# def clear_timetable(db: Session):
#     """Deletes all entries in the timetable table."""
#     logger.debug("Clearing all entries in the timetable table...")
#     db.query(TimeTable).delete()
#     db.commit()
#     logger.debug("Timetable cleared successfully.")


# def format_placeholder(entry: Dict, pengajaran_cache: Dict, timeslot_cache: Dict) -> str:
#     """Generates a placeholder string for a timetable entry."""
#     pengajaran = pengajaran_cache.get(entry["pengajaran_id"])
#     timeslot = timeslot_cache.get(entry["timeslot_id"])
#     if not pengajaran or not timeslot:
#         return ""

#     mata_kuliah = pengajaran["opened_class"].mata_kuliah_program_studi.mata_kuliah
#     placeholder = f"{timeslot.day}, ({timeslot.start_time}-{timeslot.end_time}) {mata_kuliah.namamk} {entry['kelas']}"
#     return placeholder


# ### Fetch Data ###
# def fetch_data(db: Session):
#     """Fetch and cache necessary data from the database."""
#     start_time = time.time()
#     logger.debug("Fetching data from the database...")

#     courses = db.query(MataKuliah).all()
#     lecturers = db.query(Dosen).all()
#     rooms = db.query(Ruangan).all()
#     timeslots = db.query(TimeSlot).all()
#     preferences = db.query(Preference).all()
#     opened_classes = db.query(OpenedClass).all()
#     pengajaran_list = db.query(Pengajaran).all()

#     mata_kuliah_cache = {mk.kodemk: mk for mk in courses}
#     pengajaran_cache = {
#         p.id: {
#             "dosen_id": p.dosen_id,
#             "opened_class": p.opened_class,
#             "sks": mata_kuliah_cache[p.opened_class.mata_kuliah_program_studi.mata_kuliah.kodemk].sks,
#         }
#         for p in pengajaran_list
#     }
#     room_cache = {r.id: r for r in rooms}
#     timeslot_cache = {t.id: t for t in timeslots}

#     logger.debug(f"Fetched data in {time.time() - start_time:.2f} seconds")
#     return courses, lecturers, rooms, timeslots, preferences, opened_classes, pengajaran_list, pengajaran_cache, room_cache, timeslot_cache


# ### Initialize Population ###


# def calculate_fitness(timetable: List[Dict], pengajaran_cache: Dict, room_cache: Dict) -> int:
#     """
#     Calculate fitness score for a timetable. Lower scores are better.
#     Marks entries with `is_conflicted` if they violate constraints.
#     """
#     total_penalty = 0
#     lecturer_timeslot_map = {}
#     room_timeslot_map = {}

#     # Reset conflicts for all entries
#     for entry in timetable:
#         entry["is_conflicted"] = False

#     for entry in timetable:
#         pengajaran_id = entry["pengajaran_id"]
#         ruangan_id = entry["ruangan_id"]
#         timeslot_ids = entry["timeslot_ids"]  # List of timeslots for this entry

#         pengajaran = pengajaran_cache.get(pengajaran_id)
#         if not pengajaran:
#             logger.error(f"Pengajaran not found for ID: {pengajaran_id}")
#             continue

#         lecturer_id = pengajaran["dosen_id"]

#         # Check lecturer conflicts (overlapping timeslots for the same lecturer)
#         if lecturer_id not in lecturer_timeslot_map:
#             lecturer_timeslot_map[lecturer_id] = set()
#         if any(ts_id in lecturer_timeslot_map[lecturer_id] for ts_id in timeslot_ids):
#             logger.debug(f"Lecturer conflict for lecturer {lecturer_id} in timeslots {timeslot_ids}")
#             total_penalty += 20
#             entry["is_conflicted"] = True
#         lecturer_timeslot_map[lecturer_id].update(timeslot_ids)

#         # Check room conflicts (overlapping timeslots for the same room)
#         if ruangan_id not in room_timeslot_map:
#             room_timeslot_map[ruangan_id] = set()
#         if any(ts_id in room_timeslot_map[ruangan_id] for ts_id in timeslot_ids):
#             logger.debug(f"Room conflict for room {ruangan_id} in timeslots {timeslot_ids}")
#             total_penalty += 20
#             entry["is_conflicted"] = True
#         room_timeslot_map[ruangan_id].update(timeslot_ids)

#         # Room type mismatch (room type doesn't match the course requirement)
#         room = room_cache.get(ruangan_id)
#         mata_kuliah = pengajaran["opened_class"].mata_kuliah_program_studi.mata_kuliah
#         if room and mata_kuliah and room.tipe_ruangan != mata_kuliah.tipe_mk:
#             logger.debug(f"Room type mismatch for room {ruangan_id} (type: {room.tipe_ruangan}) "
#                          f"and course {pengajaran_id} (type: {mata_kuliah.tipe_mk})")
#             total_penalty += 20
#             entry["is_conflicted"] = True

#     return total_penalty




# ### Initialize Population ###
# def initialize_population(
#     pengajaran_list, rooms, timeslots, population_size: int, pengajaran_cache: Dict
# ) -> List[Dict]:
#     """Initialize the population with random schedules."""
#     population = []
#     # Sort timeslots by ID to ensure they are in order
#     sorted_timeslots = sorted(timeslots, key=lambda x: x.id)
    
#     for _ in range(population_size):
#         timetable = []
#         for pengajaran in pengajaran_list:
#             room = random.choice(rooms)
#             sks = pengajaran_cache[pengajaran.id]["sks"]

#             # Ensure consecutive timeslots
#             available_timeslots = []
#             while len(available_timeslots) < sks:
#                 # Randomly select a starting index for consecutive timeslots
#                 start_index = random.randint(0, len(sorted_timeslots) - sks)
#                 available_timeslots = sorted_timeslots[start_index:start_index + sks]
#                 # Check if all selected timeslots are consecutive
#                 if all(available_timeslots[i].id + 1 == available_timeslots[i + 1].id for i in range(len(available_timeslots) - 1)):
#                     break
#                 else:
#                     available_timeslots = []

#             timetable.append({
#                 "pengajaran_id": pengajaran.id,
#                 "ruangan_id": room.id,
#                 "timeslot_ids": [ts.id for ts in available_timeslots],
#                 "kelas": pengajaran.opened_class.kelas,
#                 "is_conflicted": False,
#             })
#         population.append(timetable)
#     return population


# ### Evolve Population ###
# def evolve_population(population: List[List[Dict]], pengajaran_cache: Dict, room_cache: Dict, timeslots: List[TimeSlot]) -> List[List[Dict]]:
#     """Evolve the population with crossover and mutation."""
#     fitness_scores = [calculate_fitness(timetable, pengajaran_cache, room_cache) for timetable in population]
#     probabilities = [1 / score for score in fitness_scores]

#     # Sort timeslots by ID to ensure they are in order
#     sorted_timeslots = sorted(timeslots, key=lambda x: x.id)

#     # Select parents and create a new generation
#     new_population = []
#     for _ in range(len(population)):
#         parent1, parent2 = random.choices(population, weights=probabilities, k=2)
#         child = parent1[:len(parent1)//2] + parent2[len(parent2)//2:]
#         new_population.append(child)

#     # Mutation
#     for timetable in new_population:
#         if random.random() < 0.1:
#             gene = random.choice(timetable)
#             sks = pengajaran_cache[gene["pengajaran_id"]]["sks"]
#             room = random.choice(list(room_cache.values()))
#             available_timeslots = []
#             while len(available_timeslots) < sks:
#                 start_index = random.randint(0, len(sorted_timeslots) - sks)
#                 available_timeslots = sorted_timeslots[start_index:start_index + sks]
#                 # Check if all selected timeslots are consecutive
#                 if all(available_timeslots[i].id + 1 == available_timeslots[i + 1].id for i in range(len(available_timeslots) - 1)):
#                     break
#                 else:
#                     available_timeslots = []
#             gene["timeslot_ids"] = [ts.id for ts in available_timeslots]
#             gene["ruangan_id"] = room.id
#     return new_population


# ### Insert Timetable ###
# def insert_timetable(db: Session, timetable: List[Dict], pengajaran_cache: Dict, room_cache: Dict, timeslot_cache: Dict):
#     """Insert the best timetable into the database."""
#     logger.debug("Inserting timetable into the database...")
#     for entry in timetable:
#         timetable_entry = TimeTable(
#             pengajaran_id=entry["pengajaran_id"],
#             ruangan_id=entry["ruangan_id"],
#             timeslot_ids=entry["timeslot_ids"],
#             is_conflicted=entry.get("is_conflicted", False),
#             kelas=entry["kelas"],
#             kapasitas=pengajaran_cache[entry["pengajaran_id"]]["opened_class"].kapasitas,
#             academic_period_id=1,
#             placeholder=format_placeholder(entry, pengajaran_cache, timeslot_cache),
#         )
#         db.add(timetable_entry)
#     db.commit()
#     logger.debug("Timetable inserted successfully.")


# ### Genetic Algorithm ###
# def genetic_algorithm(db: Session, generations: int = 50, population_size: int = 50):
#     clear_timetable(db)
#     logger.info("Starting genetic algorithm...")

#     # Fetch data
#     _, _, rooms, timeslots, _, _, pengajaran_list, pengajaran_cache, room_cache, timeslot_cache = fetch_data(db)
#     population = initialize_population(pengajaran_list, rooms, timeslots, population_size, pengajaran_cache)

#     for generation in range(generations):
#         logger.info(f"Generation {generation + 1}/{generations}")
#         population = evolve_population(population, pengajaran_cache, room_cache, timeslots)
#         best_fitness = min(calculate_fitness(timetable, pengajaran_cache, room_cache) for timetable in population)
#         logger.info(f"Best fitness in generation {generation + 1}: {best_fitness}")

#     best_timetable = min(population, key=lambda x: calculate_fitness(x, pengajaran_cache, room_cache))
#     insert_timetable(db, best_timetable, pengajaran_cache, room_cache, timeslot_cache)
#     return best_timetable


### FastAPI Routes ###
from fastapi import APIRouter, Depends, HTTPException
from database import get_db

router = APIRouter()

@router.post("/generate-schedule")
async def generate_schedule(db: Session = Depends(get_db)):
    try:
        # best_timetable = genetic_algorithm(db)
        return {"message": "Schedule generated successfully", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset-schedule")
async def reset_schedule(db: Session = Depends(get_db)):
    try:
        # clear_timetable(db)
        return {"message": "Schedule reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))
