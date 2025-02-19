
import string
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from numpy import number
from sqlalchemy import String, or_, text
from sqlalchemy.orm import Session
# from model.matakuliah_programstudi import MataKuliahProgramStudi
from database import get_db
from routes.algorithm_routes import clear_timetable, fetch_data
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

router = APIRouter()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)



def check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache):
    """
    Check for room and lecturer conflicts in a solution.
    Returns the number of conflicts found.
    """
    conflicts = 0
    timeslot_usage = {}  
    lecturer_schedule = {}  

    for assignment in solution:
        opened_class_id, room_id, timeslot_id = assignment
        class_info = opened_class_cache[opened_class_id]
        sks = class_info['sks']
        current_timeslot = timeslot_cache[timeslot_id]

        for i in range(sks):
            current_id = timeslot_id + i
            if current_id not in timeslot_cache:
                conflicts += 1000  
                continue
                
            next_timeslot = timeslot_cache[current_id]
            if next_timeslot.day != current_timeslot.day:
                conflicts += 1000
                continue

            if current_id not in timeslot_usage:
                timeslot_usage[current_id] = []
            for used_room, _ in timeslot_usage[current_id]:
                if used_room == room_id:
                    conflicts += 1
            timeslot_usage[current_id].append((room_id, opened_class_id))

            for dosen_id in class_info['dosen_ids']:
                schedule_key = (dosen_id, current_id)
                if schedule_key in lecturer_schedule:
                    conflicts += 1
                lecturer_schedule[schedule_key] = opened_class_id

    return conflicts


def check_room_type_compatibility(solution, opened_class_cache, room_cache):
    """
    Check if room types match class types (Strict "P" <-> "P", "T" <-> "T").
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        mata_kuliah = class_info['mata_kuliah']
        room = room_cache[room_id]

        if mata_kuliah.tipe_mk == 'P' and room.tipe_ruangan != 'P':
            penalty += 1000  
        elif mata_kuliah.tipe_mk == 'T' and room.tipe_ruangan != 'T':
            penalty += 1000  

    return penalty

def check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache):
    """
    Ensure lecturers with special needs are assigned to suitable rooms.
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        room = room_cache[room_id]

        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache and preferences_cache[dosen_key].get('is_special_needs', False):
                if room.group_code not in ['KHD2', 'DS2']:
                    penalty += 1000  

    return penalty


def check_daily_load_balance(solution, opened_class_cache, timeslot_cache):
    """
    Penalize solutions where a lecturer's class assignments are heavily unbalanced across days.
    For example, if a lecturer has too many classes on one day compared to their average, we add a penalty.
    """
    penalty = 0
    # Dictionary to count number of classes per lecturer per day.
    lecturer_daily_counts = {}

    # Iterate over each assignment in the solution.
    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        # Assume each class might have multiple lecturers.
        for dosen_id in class_info['dosen_ids']:
            # Get the day from the timeslot.
            day = timeslot_cache[timeslot_id].day  # Could be a string or enum.
            if dosen_id not in lecturer_daily_counts:
                lecturer_daily_counts[dosen_id] = {}
            if day not in lecturer_daily_counts[dosen_id]:
                lecturer_daily_counts[dosen_id][day] = 0
            lecturer_daily_counts[dosen_id][day] += 1

    # Now calculate a penalty based on imbalance.
    # One simple approach: for each lecturer, calculate the average classes per day,
    # then penalize any day that deviates significantly from the average.
    for dosen_id, day_counts in lecturer_daily_counts.items():
        counts = list(day_counts.values())
        if not counts:
            continue
        avg = sum(counts) / len(counts)
        for count in counts:
            # If a day's count deviates by more than 2 classes from the average,
            # apply a penalty proportional to the deviation.
            if abs(count - avg) > 2:
                penalty += 500 * abs(count - avg)
    return penalty


def check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache):
    """
    Check if the solution complies with lecturer preferences.
    Returns a penalty score based on preference violations.
    """
    penalty = 0
    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache:
                pref_info = preferences_cache[dosen_key]
                
                if pref_info.get('is_high_priority', False):
                    # Higher penalty for scheduling during high priority times 
                    # (because these are times lecturers CANNOT teach)
                    if timeslot_id in pref_info['preferences']:
                        penalty += 800
                elif pref_info.get('used_preference', False):
                    # Normal penalty for regular preferences
                    if timeslot_id not in pref_info['preferences']:
                        penalty += 200
    
    return penalty


def calculate_fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache):
    """
    Calculate the fitness score for a solution.
    Lower scores are better.
    """
    # Conflict checking (highest priority)
    conflict_score = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache)
    if conflict_score > 0:
        return conflict_score * 1000  # Heavy penalty for conflicts

    # Room type compatibility
    room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache)

    # Preference compliance
    preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache)

    # Special needs compliance
    special_needs_penalty = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache)

    # Enforce the jabatan constraint for Senin timeslots.
    jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache)

    # Additionally, you might add your daily load balance or other soft constraints here.
    # daily_load_penalty = check_daily_load_balance(solution, opened_class_cache, timeslot_cache)

    # Total fitness: Lower is better
    return room_type_score  + preference_score + special_needs_penalty + jabatan_penalty
    # + daily_load_penalty

def generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache):
    """
    Generate a neighboring solution by making small modifications.
    Now we also randomize timeslot selection so it's not always day[0].
    """
    new_solution = current_solution.copy()

    if not new_solution:
        return new_solution

    # Pilih satu assignment secara acak
    idx = random.randrange(len(new_solution))
    opened_class_id, _, _ = new_solution[idx]
    class_info = opened_class_cache[opened_class_id]

    # Filter ruangan
    tipe_mk = class_info["mata_kuliah"].tipe_mk
    compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
    if not compatible_rooms:
        return new_solution

    # Pilih ruangan acak
    new_room = random.choice(compatible_rooms)

    # Pilih timeslot secara acak
    # (Bisa juga random shuffle + validasi SKS, tapi untuk contoh sederhana, kita random langsung)
    possible_indices = list(range(len(timeslots)))
    random.shuffle(possible_indices)

    sks = class_info["sks"]
    for start_idx in possible_indices:
        # Pastikan start_idx + sks tidak melebihi list
        if start_idx + sks > len(timeslots):
            continue

        slots = timeslots[start_idx : start_idx + sks]
        # Cek day & ID berurutan
        if all(
            slots[i].day_index == slots[0].day_index
            and slots[i].id == slots[i - 1].id + 1
            for i in range(1, sks)
        ):
            # Jika valid, assign
            new_solution[idx] = (opened_class_id, new_room.id, slots[0].id)
            break

    return new_solution

def fetch_dosen_preferences(db: Session, opened_classes):

    """
    Fetch dosen preferences and prioritize `is_high_priority=True`.
    """
    preferences_cache = {}

    for oc in opened_classes:
        

        dosen_assignments = db.query(openedclass_dosen).filter(
            openedclass_dosen.c.opened_class_id == oc.id
        ).all()

        for assignment in dosen_assignments:
            dosen_id = getattr(assignment, "pegawai_id", None)
            # logger.info(f"🔍 Checking dosen_id: {dosen_id} (type={type(dosen_id)})")  # 🔍 Debugging log
            used_preference = assignment.used_preference

            dosen_prefs = db.query(Preference).filter(
                Preference.dosen_id == dosen_id
            ).all()

            key = (oc.id, dosen_id)
            preferences_cache[key] = {
                'used_preference': used_preference,
                'preferences': {p.timeslot_id: p for p in dosen_prefs},
                'is_high_priority': any(p.is_high_priority for p in dosen_prefs),
                'is_special_needs': any(p.is_special_needs for p in dosen_prefs)
            }

    return preferences_cache

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache):
    """
    Initialize a population of valid schedules, ensuring:
    - "P" classes go to "P" rooms
    - "T" classes go to "T" rooms
    - Timeslots are allocated more randomly, so classes don't always fall on Monday.
    """
    population = []
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))

    for _ in range(population_size):
        solution = []
        room_schedule = {}
        lecturer_schedule = {}

        # Urutkan kelas berdasarkan SKS (descending)
        sorted_classes = sorted(
            opened_classes, key=lambda oc: opened_class_cache[oc.id]["sks"], reverse=True
        )

        for oc in sorted_classes:
            class_info = opened_class_cache[oc.id]
            sks = class_info["sks"]
            tipe_mk = class_info["mata_kuliah"].tipe_mk

            # Filter ruangan sesuai tipe MK
            compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
            if not compatible_rooms:
                logger.warning(f"No available room for {oc.id} ({tipe_mk})")
                continue

            assigned = False
            random.shuffle(compatible_rooms)

            # Buat daftar possible start_idx dan acak
            possible_start_idxs = list(range(len(timeslots_list) - sks + 1))
            random.shuffle(possible_start_idxs)

            for room in compatible_rooms:
                if assigned:
                    break

                for start_idx in possible_start_idxs:
                    slots = timeslots_list[start_idx : start_idx + sks]

                    # Pastikan day sama & ID berurutan
                    if not all(
                        slots[i].day_index == slots[0].day_index 
                        and slots[i].id == slots[i - 1].id + 1
                        for i in range(1, sks)
                    ):
                        continue

                    slot_available = True
                    for slot in slots:
                        # Cek ruangan
                        if (room.id, slot.id) in room_schedule:
                            slot_available = False
                            break
                        # Cek dosen
                        for dosen_id in class_info["dosen_ids"]:
                            if (dosen_id, slot.id) in lecturer_schedule:
                                slot_available = False
                                break
                        if not slot_available:
                            break

                    if slot_available:
                        # Tandai ruangan & dosen
                        for slot in slots:
                            room_schedule[(room.id, slot.id)] = oc.id
                            for dosen_id in class_info["dosen_ids"]:
                                lecturer_schedule[(dosen_id, slot.id)] = oc.id

                        solution.append((oc.id, room.id, slots[0].id))
                        assigned = True
                        break  # Selesai menempatkan kelas ini

            if not assigned:
                logger.warning(f"Could not assign class {oc.id} in initial population")

        logger.info(f"Population member has {len(solution)} assignments")
        population.append(solution)

    return population

def format_solution_for_db(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    """
    Ensure all timeslot entries are correctly formatted and inserted into the database.
    """
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found. Ensure an active period is set.")

    formatted = []
    for opened_class_id, room_id, start_timeslot_id in solution:
        try:
            class_info = opened_class_cache[opened_class_id]
            sks = class_info["sks"]
            timeslot_ids = []
            current_day = timeslot_cache[start_timeslot_id].day_index

            for i in range(sks):
                current_id = start_timeslot_id + i
                if current_id not in timeslot_cache:
                    raise ValueError(f"Invalid timeslot ID: {current_id}")
                if timeslot_cache[current_id].day_index != current_day:
                    raise ValueError(f"Timeslots cross days for class {opened_class_id}")
                timeslot_ids.append(current_id)

            timetable_entry = {
                "opened_class_id": opened_class_id,
                "ruangan_id": room_id,
                "timeslot_ids": timeslot_ids,
                "is_conflicted": True,
                "kelas": class_info["kelas"],
                "kapasitas": class_info["kapasitas"],
                "academic_period_id": active_period.id
            }
            formatted.append(timetable_entry)

        except Exception as e:
            logger.error(f"Error formatting timetable entry: {str(e)}")
            continue

    return formatted


def check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache):
    """
    Checks that if a dosen's jabatan is not null, then they are not scheduled in a timeslot on Senin (day_index == 0).
    Returns a heavy penalty for each violation.
    
    Args:
        solution: List of assignments (opened_class_id, room_id, timeslot_id)
        opened_class_cache: Dict mapping opened_class_id to class info, including list of dosen_ids.
        timeslot_cache: Dict mapping timeslot_id to timeslot details (including day_index).
        dosen_cache: Dict mapping dosen_id to the Dosen model instance (with the 'jabatan' field).
        
    Returns:
        penalty: An integer penalty to be added to the fitness score.
    """
    penalty = 0
    for opened_class_id, room_id, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        timeslot = timeslot_cache[timeslot_id]
        
        # If this timeslot is Senin (day_index 0)
        if timeslot.day_index == 0:
            for dosen_id in class_info["dosen_ids"]:
                dosen = dosen_cache.get(dosen_id)
                if dosen and dosen.jabatan is not None:
                    # Hard constraint violation: dosen with a jabatan should not be scheduled on Senin.
                    penalty += 10000
    return penalty


def simulated_annealing(db: Session, initial_temperature=1000, cooling_rate=0.95, iterations_per_temp=100):
    """
    Simulated Annealing for timetable scheduling with early stopping when fitness is 0.
    """
    clear_timetable(db)
    logger.info("🔥 Starting Simulated Annealing for scheduling...")

    # Fetch all necessary data
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    
    # Build dosen_cache using their unique pegawai_id
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}

    # Initialize first solution
    current_solution = initialize_population(opened_classes, rooms, timeslots, 1, opened_class_cache)[0]
    best_solution = current_solution
    best_fitness = calculate_fitness(
        current_solution,
        opened_class_cache,
        room_cache,
        timeslot_cache,
        preferences_cache,
        dosen_cache
    )

    temperature = initial_temperature
    iteration = 0

    # Main simulated annealing loop
    while temperature > 1:
        iteration += 1

        for i in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache)
            new_fitness = calculate_fitness(
                new_solution,
                opened_class_cache,
                room_cache,
                timeslot_cache,
                preferences_cache,
                dosen_cache
            )

            logger.debug(f"🌀 Iteration {iteration}.{i}: Temp={temperature:.2f}, Current Score={best_fitness}, New Score={new_fitness}")

            # Accept better solutions or use probability for worse ones
            if new_fitness < best_fitness:
                best_solution = new_solution
                best_fitness = new_fitness
                logger.info(f"✅ Iteration {iteration}.{i}: New Best Solution Found! Score={new_fitness}")

                # Early stopping condition if an optimal solution is found
                if best_fitness == 0:
                    logger.info("🏆 Optimal solution found with fitness 0. Stopping early!")
                    temperature = 0  # Force exit from outer loop
                    break

        # Break out of the while loop if an optimal solution was found
        if best_fitness == 0:
            break

        # Cool down the temperature
        temperature *= cooling_rate
        logger.info(f"🌡️ Cooling Down: New Temperature={temperature:.2f}")

    formatted_solution = format_solution_for_db(db, best_solution, opened_class_cache, room_cache, timeslot_cache)
    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)

    logger.info(f"🎯 Final Best Score={best_fitness}")
    return formatted_solution


def insert_timetable(db: Session, timetable: List[Dict], opened_class_cache: Dict, room_cache: Dict, timeslot_cache: Dict):
    """Insert the best timetable into the database, generating the placeholder dynamically."""
    # Fetch the active academic period
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found. Ensure an active period is set.")

    for entry in timetable:
        try:
            opened_class = opened_class_cache[entry["opened_class_id"]]
            mata_kuliah = opened_class["mata_kuliah"]
            room = room_cache[entry["ruangan_id"]]
            timeslot_ids = entry["timeslot_ids"]

            # Get the first timeslot for the class
            first_timeslot = timeslot_cache[timeslot_ids[0]]
            day = first_timeslot.day.value  # Convert DayEnum to plain string (e.g., "Senin")
            start_time = first_timeslot.start_time.strftime("%H:%M")  # Format time as string
            end_time = timeslot_cache[timeslot_ids[-1]].end_time.strftime("%H:%M")  # Format time as string

            
            placeholder = f"1. {room.kode_ruangan} - {day} ({start_time} - {end_time})"

            # If it's a kelas besar, add the second entry
            if mata_kuliah.have_kelas_besar:
                # Find the first entry of the same mata_kuliah_kodemk
                first_entry_same_kodemk = next(
                    (e for e in timetable if opened_class_cache[e["opened_class_id"]]["mata_kuliah"].kodemk == mata_kuliah.kodemk),
                    None
                )

                if first_entry_same_kodemk:
                    first_entry_timeslot = timeslot_cache[first_entry_same_kodemk["timeslot_ids"][0]]
                    first_entry_day = first_entry_timeslot.day.value  
                    first_entry_start_time = first_entry_timeslot.start_time.strftime("%H:%M")  
                    first_entry_end_time = timeslot_cache[first_entry_same_kodemk["timeslot_ids"][-1]].end_time.strftime("%H:%M")  # Format time as string

                    # Add the second placeholder entry
                    placeholder += f"\n2. FIK-VCR-KB-1 - {first_entry_day} ({first_entry_start_time} - {first_entry_end_time})"

            # Create the TimeTable entry
            timetable_entry = TimeTable(
                opened_class_id=entry["opened_class_id"],
                ruangan_id=entry["ruangan_id"],
                timeslot_ids=entry["timeslot_ids"],
                is_conflicted=True,
                # is_conflicted=entry["is_conflicted"],
                kelas=entry["kelas"],
                kapasitas=opened_class["kapasitas"],
                academic_period_id=active_period.id,  # Use the active academic period's ID
                placeholder=placeholder,  # Add the dynamically generated placeholder
            )
            db.add(timetable_entry)
        except KeyError as e:
            logger.error(f"Missing key in opened_class_cache or room_cache for timetable entry: {e}")
            continue

    db.commit()

@router.post("/generate-schedule-sa")
async def generate_schedule_sa(db: Session = Depends(get_db)):
    try:
        logger.info("Generating schedule using Simulated Annealing...")
        best_timetable = simulated_annealing(db)
        return {"message": "Schedule generated successfully using Simulated Annealing", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))