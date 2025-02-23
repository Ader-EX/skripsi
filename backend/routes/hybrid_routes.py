import random
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from routes.ga_routes import check_conflicts
from routes.sa_routes import check_jabatan_constraint, check_preference_compliance, check_room_type_compatibility, check_special_needs_compliance, get_effective_sks, identify_recess_times
from database import get_db
from routes.algorithm_routes import clear_timetable, fetch_data
from model.academicperiod_model import AcademicPeriods
from model.user_model import User
from model.matakuliah_model import MataKuliah
from model.dosen_model import Dosen
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass, openedclass_dosen
from model.timetable_model import TimeTable

router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)



def fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache):
    conflict_score = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache)
    if conflict_score > 0:
        return conflict_score * 20
    room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache)
    special_needs_score = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache)
    preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache)
    jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache)
    return room_type_score + special_needs_score + preference_score + jabatan_penalty

def generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times):
    new_solution = current_solution.copy()
    if not new_solution:
        return new_solution
    idx = random.randrange(len(new_solution))
    opened_class_id, _, _ = new_solution[idx]
    class_info = opened_class_cache[opened_class_id]
    tipe_mk = class_info["mata_kuliah"].tipe_mk
    compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
    if not compatible_rooms:
        return new_solution
    new_room = random.choice(compatible_rooms)
    effective_sks = get_effective_sks(class_info)
    possible_indices = list(range(len(timeslots)))
    random.shuffle(possible_indices)
    for start_idx in possible_indices:
        if start_idx + effective_sks > len(timeslots):
            continue
        slots = timeslots[start_idx: start_idx + effective_sks]
        if all(
            slots[i].day_index == slots[0].day_index and 
            slots[i].id == slots[i - 1].id + 1 and 
            slots[i].start_time == slots[i - 1].end_time and 
            slots[i].id not in recess_times
            for i in range(1, effective_sks)
        ):
            new_solution[idx] = (opened_class_id, new_room.id, slots[0].id)
            break
    return new_solution

def format_solution_for_db(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found. Ensure an active period is set.")
    formatted = []
    for opened_class_id, room_id, start_timeslot_id in solution:
        try:
            class_info = opened_class_cache[opened_class_id]
            effective_sks = get_effective_sks(class_info)
            timeslot_ids = []
            current_day = timeslot_cache[start_timeslot_id].day_index
            for i in range(effective_sks):
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

def insert_timetable(db: Session, timetable: List[Dict], opened_class_cache, room_cache, timeslot_cache):
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found. Ensure an active period is set.")
    for entry in timetable:
        try:
            opened_class = opened_class_cache[entry["opened_class_id"]]
            mata_kuliah = opened_class["mata_kuliah"]
            room = room_cache[entry["ruangan_id"]]
            timeslot_ids = entry["timeslot_ids"]
            first_timeslot = timeslot_cache[timeslot_ids[0]]
            day = first_timeslot.day.value
            start_time = first_timeslot.start_time.strftime("%H:%M")
            end_time = timeslot_cache[timeslot_ids[-1]].end_time.strftime("%H:%M")
            placeholder = f"1. {room.kode_ruangan} - {day} ({start_time} - {end_time})"
            if mata_kuliah.have_kelas_besar:
                first_entry_same_kodemk = next(
                    (e for e in timetable if opened_class_cache[e["opened_class_id"]]["mata_kuliah"].kodemk == mata_kuliah.kodemk),
                    None
                )
                if first_entry_same_kodemk:
                    first_entry_timeslot = timeslot_cache[first_entry_same_kodemk["timeslot_ids"][0]]
                    first_entry_day = first_entry_timeslot.day.value  
                    first_entry_start_time = first_entry_timeslot.start_time.strftime("%H:%M")  
                    first_entry_end_time = timeslot_cache[first_entry_same_kodemk["timeslot_ids"][-1]].end_time.strftime("%H:%M")
                    placeholder += f"\n2. FIK-VCR-KB-1 - {first_entry_day} ({first_entry_start_time} - {first_entry_end_time})"
            timetable_entry = TimeTable(
                opened_class_id=entry["opened_class_id"],
                ruangan_id=entry["ruangan_id"],
                timeslot_ids=entry["timeslot_ids"],
                is_conflicted=entry["is_conflicted"],
                kelas=entry["kelas"],
                kapasitas=opened_class["kapasitas"],
                academic_period_id=active_period.id,
                placeholder=placeholder,
            )
            db.add(timetable_entry)
        except KeyError as e:
            logger.error(f"Missing key in opened_class_cache or room_cache for timetable entry: {e}")
            continue
    db.commit()


# =============================================================================
#                        GA SUPPORT FUNCTIONS
# =============================================================================

def selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, k=3):
    selected = []
    for _ in range(len(population)):
        candidates = random.sample(population, k)
        best_candidate = min(
            candidates,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
        )
        selected.append(best_candidate)
    return selected

def crossover(parent1, parent2):
    if len(parent1) == 0 or len(parent2) == 0:
        return parent1, parent2
    point = random.randint(1, min(len(parent1), len(parent2)) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

def mutate(solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times, mutation_prob=0.1):
    new_solution = solution.copy()
    if not new_solution:
        return new_solution
    if random.random() < mutation_prob:
        idx = random.randrange(len(new_solution))
        opened_class_id, _, _ = new_solution[idx]
        class_info = opened_class_cache[opened_class_id]
        effective_sks = get_effective_sks(class_info)
        tipe_mk = class_info["mata_kuliah"].tipe_mk
        compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
        if compatible_rooms:
            new_room = random.choice(compatible_rooms)
            valid_timeslots = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))
            possible_indices = list(range(len(valid_timeslots) - effective_sks + 1))
            random.shuffle(possible_indices)
            for start_idx in possible_indices:
                slots = valid_timeslots[start_idx : start_idx + effective_sks]
                if all(
                    slots[i].day_index == slots[0].day_index and
                    slots[i].id == slots[i-1].id + 1 and
                    slots[i].id not in recess_times
                    for i in range(1, effective_sks)
                ):
                    new_solution[idx] = (opened_class_id, new_room.id, slots[0].id)
                    logger.info(f"Mutation: Class {opened_class_id} moved to Room {new_room.id}, Timeslot {slots[0].id}")
                    break
    return new_solution

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times):
    population = []
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))
    
    for _ in range(population_size):
        solution = []
        room_schedule = {}      # Tracks which room slots are taken
        lecturer_schedule = {}  # Tracks which lecturer slots are taken
        
        # Sort classes by effective SKS in descending order
        sorted_classes = sorted(
            opened_classes, key=lambda oc: get_effective_sks(opened_class_cache[oc.id]), reverse=True
        )
        
        for oc in sorted_classes:
            class_info = opened_class_cache[oc.id]
            effective_sks = get_effective_sks(class_info)
            tipe_mk = class_info["mata_kuliah"].tipe_mk
            compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
            if not compatible_rooms:
                logger.warning(f"No available room for class {oc.id} ({tipe_mk})")
                continue
            
            assigned = False
            random.shuffle(compatible_rooms)
            possible_start_idxs = list(range(len(timeslots_list) - effective_sks + 1))
            random.shuffle(possible_start_idxs)
            
            # First, try to find a conflict-free assignment.
            for room in compatible_rooms:
                if assigned:
                    break
                for start_idx in possible_start_idxs:
                    slots = timeslots_list[start_idx : start_idx + effective_sks]
                    if not all(
                        slots[i].day_index == slots[0].day_index and 
                        slots[i].id == slots[i-1].id + 1 and
                        slots[i].id not in recess_times
                        for i in range(1, effective_sks)
                    ):
                        continue
                    
                    # Check if these slots are available for both room and lecturers.
                    slot_available = True
                    for slot in slots:
                        if (room.id, slot.id) in room_schedule:
                            slot_available = False
                            break
                        for dosen_id in class_info["dosen_ids"]:
                            if (dosen_id, slot.id) in lecturer_schedule:
                                slot_available = False
                                break
                        if not slot_available:
                            break
                    
                    if slot_available:
                        for slot in slots:
                            room_schedule[(room.id, slot.id)] = oc.id
                            for dosen_id in class_info["dosen_ids"]:
                                lecturer_schedule[(dosen_id, slot.id)] = oc.id
                        solution.append((oc.id, room.id, slots[0].id))
                        assigned = True
                        break
            
            # Fallback: If no conflict-free assignment was found, choose the option with the fewest conflicts.
            if not assigned:
                logger.warning(f"Conflict-free assignment not found for class {oc.id}; applying fallback.")
                best_conflict = float('inf')
                best_assignment = None
                best_slots = None
                best_room = None
                for room in compatible_rooms:
                    for start_idx in possible_start_idxs:
                        slots = timeslots_list[start_idx : start_idx + effective_sks]
                        if not all(
                            slots[i].day_index == slots[0].day_index and 
                            slots[i].id == slots[i-1].id + 1 and
                            slots[i].id not in recess_times
                            for i in range(1, effective_sks)
                        ):
                            continue
                        conflict_cost = 0
                        for slot in slots:
                            if (room.id, slot.id) in room_schedule:
                                conflict_cost += 1
                            for dosen_id in class_info["dosen_ids"]:
                                if (dosen_id, slot.id) in lecturer_schedule:
                                    conflict_cost += 1
                        if conflict_cost < best_conflict:
                            best_conflict = conflict_cost
                            best_assignment = (oc.id, room.id, slots[0].id)
                            best_slots = slots
                            best_room = room
                if best_assignment:
                    for slot in best_slots:
                        room_schedule[(best_room.id, slot.id)] = oc.id
                        for dosen_id in class_info["dosen_ids"]:
                            lecturer_schedule[(dosen_id, slot.id)] = oc.id
                    solution.append(best_assignment)
                    logger.info(f"Fallback: Assigned class {oc.id} with conflict cost {best_conflict}")
                else:
                    logger.warning(f"Could not assign class {oc.id} even with fallback.")
        population.append(solution)
    return population

def fetch_dosen_preferences(db: Session, opened_classes: List[OpenedClass]):
    preferences_cache = {}
    for oc in opened_classes:
        dosen_assignments = db.query(openedclass_dosen).filter(
            openedclass_dosen.c.opened_class_id == oc.id
        ).all()
        for assignment in dosen_assignments:
            dosen_id = getattr(assignment, "pegawai_id", None)
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


# =============================================================================
#                        HYBRID GA + SA FUNCTION
# =============================================================================

def hybrid_schedule(
    db: Session,
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.1,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100
):
    # Clear previous schedule and fetch all necessary data once.
    clear_timetable(db)
    logger.info("Starting Hybrid GA-SA scheduling...")
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}
    recess_times = identify_recess_times(timeslot_cache)

    # ------------------------- GA Phase -------------------------
    population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times)
    for gen in range(generations):
        selected_pop = selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, k=3)
        new_population = []
        for i in range(0, len(selected_pop), 2):
            if i + 1 < len(selected_pop):
                child1, child2 = crossover(selected_pop[i], selected_pop[i+1])
                new_population.extend([child1, child2])
            else:
                new_population.append(selected_pop[i])
        mutated_population = []
        for indiv in new_population:
            mutated_indiv = mutate(indiv, opened_classes, rooms, timeslots, opened_class_cache, recess_times, mutation_prob)
            mutated_population.append(mutated_indiv)
        population = mutated_population

        best_solution_ga = min(
            population,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
        )
        best_fitness_ga = fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
        logger.info(f"GA Generation {gen+1}: Best fitness = {best_fitness_ga}")
        if best_fitness_ga == 0:
            logger.info("Optimal GA solution found; stopping GA early.")
            population = [best_solution_ga]
            break

    best_solution_ga = min(
        population,
        key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
    )
    logger.info(f"GA phase completed with best fitness = {fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)}")
    
    # ------------------------- SA Phase -------------------------
    # Use the best GA solution as the initial solution for SA
    current_solution = best_solution_ga
    current_fitness = fitness(current_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
    temperature = initial_temperature
    best_solution_sa = current_solution
    best_fitness_sa = current_fitness

    iteration = 0
    while temperature > 1:
        iteration += 1
        for i in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times)
            new_fitness = fitness(new_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
            if new_fitness < current_fitness:
                current_solution = new_solution
                current_fitness = new_fitness
                if current_fitness < best_fitness_sa:
                    best_solution_sa = current_solution
                    best_fitness_sa = current_fitness
                    logger.info(f"SA Iteration {iteration}.{i}: New best fitness = {new_fitness}")
                    if best_fitness_sa == 0:
                        temperature = 0
                        break
        if best_fitness_sa == 0:
            break
        temperature *= cooling_rate
        logger.info(f"SA Cooling: Temperature now = {temperature:.2f}")

    # ------------------------- Finalize -------------------------
    formatted_solution = format_solution_for_db(db, best_solution_sa, opened_class_cache, room_cache, timeslot_cache)
    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)
    logger.info(f"Hybrid GA-SA scheduling completed with final best fitness = {best_fitness_sa}")
    return formatted_solution


# =============================================================================
#                        HYBRID GA-SA ENDPOINT
# =============================================================================

@router.post("/generate-schedule-hybrid")
async def generate_schedule_hybrid(
    db: Session = Depends(get_db),
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.1,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100
):
    try:
        best_timetable = hybrid_schedule(
            db=db,
            population_size=population_size,
            generations=generations,
            mutation_prob=mutation_prob,
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            iterations_per_temp=iterations_per_temp
        )
        return {
            "message": "Schedule generated successfully using Hybrid GA-SA",
            "timetable": best_timetable
        }
    except Exception as e:
        logger.error(f"Error generating schedule with Hybrid GA-SA: {e}")
        raise HTTPException(status_code=500, detail=str(e))
