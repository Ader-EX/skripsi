
import string
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from numpy import number
from sqlalchemy import String, or_, text
from sqlalchemy.orm import Session
# from model.matakuliah_programstudi import MataKuliahProgramStudi
from database import get_db
from routes.algorithm_routes import clear_timetable, fetch_data, insert_timetable
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
    timeslot_usage = {}  # {timeslot_id: [(room_id, opened_class_id)]}
    lecturer_schedule = {}  # {(dosen_id, timeslot_id): opened_class_id}
    
    for assignment in solution:
        opened_class_id, room_id, timeslot_id = assignment
        class_info = opened_class_cache[opened_class_id]
        sks = class_info['sks']
        
        # Check consecutive timeslots within the same day
        current_timeslot = timeslot_cache[timeslot_id]
        for i in range(sks):
            current_id = timeslot_id + i
            if current_id not in timeslot_cache:
                conflicts += 1000  # Heavy penalty for invalid timeslot
                continue
                
            # Check if we're crossing days
            next_timeslot = timeslot_cache[current_id]
            if next_timeslot.day != current_timeslot.day:
                conflicts += 1000
                continue
            
            # Check room conflicts
            if current_id not in timeslot_usage:
                timeslot_usage[current_id] = []
            for used_room, _ in timeslot_usage[current_id]:
                if used_room == room_id:
                    conflicts += 1
            timeslot_usage[current_id].append((room_id, opened_class_id))
            
            # Check lecturer conflicts
            for dosen_id in class_info['dosen_ids']:
                schedule_key = (dosen_id, current_id)
                if schedule_key in lecturer_schedule:
                    conflicts += 1
                lecturer_schedule[schedule_key] = opened_class_id

    return conflicts

def check_room_type_compatibility(solution, opened_class_cache, room_cache):
    """
    Check if room types match class types with stricter penalties.
    Returns a penalty score based on mismatches.
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        mata_kuliah = class_info['mata_kuliah']
        room = room_cache[room_id]
        
        # Check room type compatibility
        if mata_kuliah.tipe_mk == 'P':  # Practical class
            if room.tipe_ruangan == 'P':
                continue  # Perfect match, no penalty
            elif room.tipe_ruangan == 'T':
                penalty += 500  # Heavy penalty for using theory room
            else:
                penalty += 1000  # Very heavy penalty for using special rooms
        elif mata_kuliah.tipe_mk == 'T':  # Theory class
            if room.tipe_ruangan == 'T':
                continue  # Perfect match, no penalty
            elif room.tipe_ruangan == 'P':
                penalty += 1000  # Very heavy penalty for using practical room
            else:
                penalty += 1000  # Very heavy penalty for using special rooms
        elif mata_kuliah.tipe_mk == 'S':  # Special class
            if room.tipe_ruangan != 'S':
                penalty += 1000  # Must use special rooms
    
    return penalty

def check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache):
    """
    Check if the solution complies with special needs requirements.
    Returns a penalty score based on violations.
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        room = room_cache[room_id]
        
        # Check for lecturers with special needs
        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache:
                pref_info = preferences_cache[dosen_key]
                if pref_info.get('is_special_needs', False):
                    # Check if room is in KHD2 or DS2
                    if room.group_code not in ['KHD2', 'DS2']:
                        penalty += 1000  # Heavy penalty for non-accessible rooms
    
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
                    # Higher penalty for violating high priority preferences
                    if timeslot_id not in pref_info['preferences']:
                        penalty += 800
                elif pref_info.get('used_preference', False):
                    # Normal penalty for regular preferences
                    if timeslot_id not in pref_info['preferences']:
                        penalty += 200
    
    return penalty

def calculate_fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache):
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
    
    return room_type_score + preference_score

def generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache):
    """
    Generate a neighboring solution by making small modifications.
    """
    new_solution = current_solution.copy()
    
    # Randomly select an opened class to modify
    idx = random.randrange(len(new_solution))
    opened_class_id, _, _ = new_solution[idx]
    class_info = opened_class_cache[opened_class_id]
    
    # Try to find a valid room and timeslot combination
    compatible_rooms = [r for r in rooms if r.tipe_ruangan != 'S' or 
                       r.tipe_ruangan == class_info['mata_kuliah'].tipe_mk]
    
    if compatible_rooms:
        new_room = random.choice(compatible_rooms)
        # Find valid consecutive timeslots within the same day
        valid_start_slots = []
        current_day = None
        consecutive_count = 0
        
        for i, slot in enumerate(timeslots):
            if current_day != slot.day:
                current_day = slot.day
                consecutive_count = 1
            else:
                consecutive_count += 1
            
            if consecutive_count >= class_info['sks']:
                valid_start_slots.append(i - class_info['sks'] + 1)
        
        if valid_start_slots:
            start_slot = timeslots[random.choice(valid_start_slots)]
            new_solution[idx] = (opened_class_id, new_room.id, start_slot.id)
    
    return new_solution

def fetch_dosen_preferences(db: Session, opened_classes):
    """
    Fetch dosen preferences and their used_preference status from the openedclass_dosen table.
    """
    preferences_cache = {}
    
    for oc in opened_classes:
        # Query the openedclass_dosen association table directly
        dosen_assignments = db.query(openedclass_dosen).filter(
            openedclass_dosen.c.opened_class_id == oc.id
        ).all()
        
        for assignment in dosen_assignments:
            dosen_id = assignment.dosen_id
            used_preference = assignment.used_preference
            
            # Get preferences for this dosen
            dosen_prefs = db.query(Preference).filter(
                Preference.dosen_id == dosen_id
            ).all()
            
            key = (oc.id, dosen_id)
            preferences_cache[key] = {
                'used_preference': used_preference,
                'preferences': {p.timeslot_id: p for p in dosen_prefs},
                'is_high_priority': any(p.is_high_priority for p in dosen_prefs)
            }
    
    return preferences_cache

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache):
    """
    Initialize a population of valid solutions with minimal conflicts.
    Each solution is a list of tuples (opened_class_id, room_id, timeslot_id).
    """
    population = []
    timeslots_list = sorted(timeslots, key=lambda x: (x.day, x.start_time))
    
    for _ in range(population_size):
        solution = []
        room_schedule = {}  # {(room_id, timeslot_id): opened_class_id}
        lecturer_schedule = {}  # {(dosen_id, timeslot_id): opened_class_id}
        
        # Sort opened classes by constraints (more constrained first)
        sorted_classes = sorted(
            [oc for oc in opened_classes if oc.id in opened_class_cache],
            key=lambda x: (
                opened_class_cache[x.id]['sks'],  # Classes with more hours first
                len(opened_class_cache[x.id]['dosen_ids'])  # Classes with more lecturers first
            ),
            reverse=True
        )
        
        for oc in sorted_classes:
            try:
                class_info = opened_class_cache[oc.id]
                sks = class_info['sks']
                
                # Filter compatible rooms
                compatible_rooms = [r for r in rooms 
                                  if (r.tipe_ruangan == class_info['mata_kuliah'].tipe_mk) or
                                     (r.tipe_ruangan != 'S' and class_info['mata_kuliah'].tipe_mk != 'S')]
                
                if not compatible_rooms:
                    continue
                
                # Try each room and timeslot combination
                assigned = False
                random.shuffle(compatible_rooms)  # Add randomness to room selection
                
                for room in compatible_rooms:
                    if assigned:
                        break
                        
                    # Find valid timeslot sequences
                    for start_idx in range(len(timeslots_list) - sks + 1):
                        slots = timeslots_list[start_idx:start_idx + sks]
                        
                        # Check if slots are consecutive and in same day
                        if not all(slots[i].day == slots[0].day and 
                                 slots[i].id == slots[i-1].id + 1 
                                 for i in range(1, len(slots))):
                            continue
                        
                        # Check room and lecturer availability
                        slot_available = True
                        for slot in slots:
                            # Check room conflict
                            if (room.id, slot.id) in room_schedule:
                                slot_available = False
                                break
                                
                            # Check lecturer conflicts
                            for dosen_id in class_info['dosen_ids']:
                                if (dosen_id, slot.id) in lecturer_schedule:
                                    slot_available = False
                                    break
                        
                        if slot_available:
                            # Add to schedules
                            for slot in slots:
                                room_schedule[(room.id, slot.id)] = oc.id
                                for dosen_id in class_info['dosen_ids']:
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

def format_solution_for_db(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    """
    Convert solution tuples to database-compatible format for TimeTable model.
    Fetches the currently active academic period dynamically.
    """
    # Fetch the active academic period
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    
    if not active_period:
        raise ValueError("No active academic period found. Please ensure an academic period is set as active.")

    formatted = []
    for opened_class_id, room_id, start_timeslot_id in solution:
        try:
            # Get class info
            class_info = opened_class_cache[opened_class_id]
            sks = class_info['sks']
            
            # Generate list of consecutive timeslot IDs
            timeslot_ids = []
            current_day = timeslot_cache[start_timeslot_id].day
            
            for i in range(sks):
                current_id = start_timeslot_id + i
                if current_id not in timeslot_cache:
                    raise ValueError(f"Invalid timeslot ID: {current_id}")
                if timeslot_cache[current_id].day != current_day:
                    raise ValueError(f"Timeslots cross days for class {opened_class_id}")
                timeslot_ids.append(current_id)
            
            # ✅ Use dynamically fetched academic_period_id
            timetable_entry = {
                'opened_class_id': opened_class_id,
                'ruangan_id': room_id,
                'timeslot_ids': timeslot_ids,
                'is_conflicted': True,  # Conflict detection logic should update this later
                'kelas': class_info['kelas'],
                'kapasitas': class_info['kapasitas'],
                'academic_period_id': active_period.id  # ✅ Now dynamic!
            }
            formatted.append(timetable_entry)
            
        except Exception as e:
            logger.error(f"Error formatting timetable entry: {str(e)}")
            continue
    
    return formatted


def simulated_annealing(
    db: Session,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100
):
    """Enhanced Simulated Annealing algorithm for scheduling."""
    clear_timetable(db)
    logger.info("Starting Simulated Annealing for scheduling...")
    
    # Fetch required data
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    
    # Create preferences cache using the new function
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    
    # Generate initial solution
    current_solution = initialize_population(opened_classes, rooms, timeslots, 1, opened_class_cache)[0]
    current_fitness = calculate_fitness(current_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache)
    best_solution = current_solution
    best_fitness = current_fitness
    temperature = initial_temperature
    
    while temperature > 1:
        for _ in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache)
            new_fitness = calculate_fitness(new_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache)
            
            # Calculate acceptance probability
            if new_fitness < current_fitness:
                acceptance_probability = 1.0
            else:
                acceptance_probability = math.exp((current_fitness - new_fitness) / temperature)
            
            if random.random() < acceptance_probability:
                current_solution = new_solution
                current_fitness = new_fitness
                
                if current_fitness < best_fitness:
                    best_solution = current_solution
                    best_fitness = current_fitness
                    logger.debug(f"New Best Fitness: {best_fitness}")
        
        temperature *= cooling_rate
        logger.info(f"Temperature: {temperature:.2f}, Best Fitness: {best_fitness}")
    
    # Format and insert final solution into database
    formatted_solution = format_solution_for_db(db, best_solution, opened_class_cache, room_cache, timeslot_cache)

    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)
    return formatted_solution

@router.post("/generate-schedule-sa")
async def generate_schedule_sa(db: Session = Depends(get_db)):
    try:
        logger.info("Generating schedule using Simulated Annealing...")
        best_timetable = simulated_annealing(db)
        return {"message": "Schedule generated successfully using Simulated Annealing", "timetable": best_timetable}
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))