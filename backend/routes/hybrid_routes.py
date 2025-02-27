import random
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from routes.sa_routes import get_effective_sks, identify_recess_times
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


def check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache, penalties):
    conflicts = 0
    timeslot_usage = {}  
    lecturer_schedule = {}  

    for assignment in solution:
        opened_class_id, room_id, timeslot_id = assignment
        class_info = opened_class_cache[opened_class_id]

        effective_sks = get_effective_sks(class_info)
        current_timeslot = timeslot_cache[timeslot_id]

        for i in range(effective_sks):
            current_id = timeslot_id + i
            if current_id not in timeslot_cache:
                conflicts += penalties["invalid_timeslot"]  # Penalti timeslot invalid
                continue

            next_timeslot = timeslot_cache[current_id]
            if next_timeslot.day != current_timeslot.day:
                conflicts += penalties["cross_day"]  # Penalti loncat hari
                continue

            if current_id not in timeslot_usage:
                timeslot_usage[current_id] = []
            for used_room, _ in timeslot_usage[current_id]:
                if used_room == room_id:
                    conflicts += penalties["room_conflict"]  # Penalty ruangan bentrok
            timeslot_usage[current_id].append((room_id, opened_class_id))

            for dosen_id in class_info['dosen_ids']:
                schedule_key = (dosen_id, current_id)
                if schedule_key in lecturer_schedule:
                    conflicts += penalties["lecturer_conflict"]  # Penalty for dosen bntrok
                lecturer_schedule[schedule_key] = opened_class_id

    return conflicts



def check_room_type_compatibility(solution, opened_class_cache, room_cache, penalties):
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        mata_kuliah = class_info['mata_kuliah']
        room = room_cache[room_id]

        if mata_kuliah.tipe_mk == 'P' and room.tipe_ruangan != 'P':
            penalty += penalties["wrong_room"]
        elif mata_kuliah.tipe_mk == 'T' and room.tipe_ruangan != 'T':
            penalty += penalties["wrong_room"]
        elif mata_kuliah.tipe_mk == 'S' and room.tipe_ruangan != 'S':
            penalty += penalties["wrong_room"]    

    return penalty

def check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache, penalties):
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        room = room_cache[room_id]

        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache and preferences_cache[dosen_key].get('is_special_needs', False):
                if room.group_code not in ['KHD2', 'DS2']:
                    penalty += penalties["special_needs"]
    return penalty


def check_daily_load_balance(solution, opened_class_cache, timeslot_cache, penalties):
    penalty = 0
    lecturer_daily_counts = {}

    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        for dosen_id in class_info['dosen_ids']:
            day = timeslot_cache[timeslot_id].day
            if dosen_id not in lecturer_daily_counts:
                lecturer_daily_counts[dosen_id] = {}
            if day not in lecturer_daily_counts[dosen_id]:
                lecturer_daily_counts[dosen_id][day] = 0
            lecturer_daily_counts[dosen_id][day] += 1

    for dosen_id, day_counts in lecturer_daily_counts.items():
        counts = list(day_counts.values())
        if not counts:
            continue
        avg = sum(counts) / len(counts)
        for count in counts:
            if abs(count - avg) > 2:
                penalty += penalties["daily_load"] * abs(count - avg)
    return penalty


def check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache, penalties):
    penalty = 0
    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache:
                pref_info = preferences_cache[dosen_key]
                if pref_info.get('is_high_priority', False):
                    if timeslot_id not in pref_info['preferences']:
                        penalty += penalties["high_priority_preference"]
                elif pref_info.get('used_preference', False):
                    if timeslot_id not in pref_info['preferences']:
                        penalty += penalties["general_preference"]
    return penalty




def check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache, penalties):
    penalty = 0
    for opened_class_id, room_id, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        timeslot = timeslot_cache[timeslot_id]
        
        if timeslot.day_index == 0:
            for dosen_id in class_info["dosen_ids"]:
                dosen = dosen_cache.get(dosen_id)
                if dosen and dosen.jabatan is not None:
                    penalty += penalties["jabatan"]
    return penalty

def fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties):
    conflict_score = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache, penalties)
    if conflict_score > 0:
        return conflict_score * penalties["conflict_multiplier"]
    room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache, penalties)
    special_needs_score = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache, penalties)
    daily_load_score = check_daily_load_balance(solution, opened_class_cache, timeslot_cache, penalties)
    preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache, penalties)
    jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache, penalties)
    return room_type_score + special_needs_score + daily_load_score + preference_score + jabatan_penalty

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

def selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties,k=3,):
    selected = []
    for _ in range(len(population)):
        candidates = random.sample(population, k)
        best_candidate = min(
            candidates,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache,penalties)
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
                    logger.info(f"Mutasi: kelas {opened_class_id} pindah ke ruangan {new_room.id}, dg timeslot {slots[0].id}")
                    break
    return new_solution

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times):
    # Fungsi ini buat bikin populasi solusi jadwal kelas. Kita mulai dengan urutin timeslot berdasarkan hari dan jam
    # biar gampang nyesuain jadwalnya. Setiap individu di populasi bakal punya jadwal yang kita atur secara random 
    # berdasarkan kelas-kelas yang udah dibuka, ruangan yang tersedia, dan dosen yang ada. Tujuan kita adalah 
    # untuk nyocokin kelas dengan ruangan dan timeslot, tapi pastikan gak ada bentrok, baik itu ruangan atau dosen.
    population = []  
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))  # Urutin timeslot berdasarkan hari dan jam mulai
    
    # Proses untuk nyiptain banyak solusi (populasi solusi)
    for _ in range(population_size):  
        solution = []  # Setiap solusi bakal nyimpen jadwal untuk satu individu
        room_schedule = {}  # Nyimpen jadwal ruangan
        lecturer_schedule = {}  # Nyimpen jadwal dosen
        
        # Urutin kelas yang buka berdasarkan SKS efektifnya, jadi kelas yang punya beban lebih berat diutamakan
        sorted_classes = sorted(
            opened_classes, key=lambda oc: get_effective_sks(opened_class_cache[oc.id]), reverse=True
        )
        
        # Loop buat nyusun jadwal tiap kelas
        for oc in sorted_classes:
            class_info = opened_class_cache[oc.id]  # Ambil info kelas dari cache
            effective_sks = get_effective_sks(class_info)  # Dapetin jumlah SKS yang efektif
            tipe_mk = class_info["mata_kuliah"].tipe_mk  # Ambil tipe mata kuliah
            compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]  # Cari ruangan yang cocok sama tipe mata kuliah
            if not compatible_rooms:  # Kalau nggak ada ruangan yang cocok, langsung skip kelas ini
                logger.warning(f"Kelas {oc.id} ({tipe_mk}) nggak punya ruangan yang sesuai.")
                continue  # Langsung lanjut ke kelas berikutnya
            
            assigned = False  # Tandai apakah kelas udah dapet jadwal atau belum
            random.shuffle(compatible_rooms)  # Acak urutan ruangan supaya nggak selalu sama
            possible_start_idxs = list(range(len(timeslots_list) - effective_sks + 1))  
            random.shuffle(possible_start_idxs)  # Acak index timeslot supaya lebih random
            
            # Coba cari ruangan yang cocok dan timeslot yang available
            for room in compatible_rooms:
                if assigned:
                    break  # Kalau kelas udah terjadwal, nggak usah coba-coba lagi
                for start_idx in possible_start_idxs:
                    slots = timeslots_list[start_idx : start_idx + effective_sks]  # Ambil timeslot untuk kelas ini
                    
                    # Cek apakah slot valid: hari sama, urutan timeslotnya bener, dan nggak ada di waktu istirahat
                    if not all(
                        slots[i].day_index == slots[0].day_index and 
                        slots[i].id == slots[i-1].id + 1 and
                        slots[i].id not in recess_times
                        for i in range(1, effective_sks)
                    ):
                        continue
                    
                    # Cek apakah slot ini udah dipakai atau belum, baik untuk ruangan dan dosen
                    slot_available = True
                    for slot in slots:
                        if (room.id, slot.id) in room_schedule or any(
                            (dosen_id, slot.id) in lecturer_schedule for dosen_id in class_info["dosen_ids"]
                        ):
                            slot_available = False
                            break
                    
                    # Kalau slot tersedia, assign jadwalnya ke ruangan dan dosen
                    if slot_available:
                        for slot in slots:
                            room_schedule[(room.id, slot.id)] = oc.id
                            for dosen_id in class_info["dosen_ids"]:
                                lecturer_schedule[(dosen_id, slot.id)] = oc.id
                        solution.append((oc.id, room.id, slots[0].id))  # Simpan hasil penugasan
                        assigned = True  # Tandai kelas udah terjadwal
                        break
            
            # Kalau sampai sini kelas masih belum terjadwal, coba fallback
            if not assigned:
                logger.warning(f"Jadwal nggak ketemu buat kelas {oc.id}, coba fallback dengan minim konflik.")
                best_conflict = float('inf')  # Kita coba cari solusi dengan konflik paling sedikit
                best_assignment = None
                best_slots = None
                best_room = None
                
                # Coba semua kemungkinan ruangan dan timeslot untuk fallback
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
                        
                        # Hitung jumlah konflik (berapa kali bentrok dengan jadwal yang udah ada)
                        conflict_cost = sum(
                            (room.id, slot.id) in room_schedule or any(
                                (dosen_id, slot.id) in lecturer_schedule for dosen_id in class_info["dosen_ids"]
                            ) for slot in slots
                        )
                        
                        # Pilih jadwal dengan konflik paling sedikit
                        if conflict_cost < best_conflict:
                            best_conflict = conflict_cost
                            best_assignment = (oc.id, room.id, slots[0].id)
                            best_slots = slots
                            best_room = room
                
                # Kalau ada solusi fallback dengan konflik lebih kecil, kita pake itu
                if best_assignment:
                    for slot in best_slots:
                        room_schedule[(best_room.id, slot.id)] = oc.id
                        for dosen_id in class_info["dosen_ids"]:
                            lecturer_schedule[(dosen_id, slot.id)] = oc.id
                    solution.append(best_assignment)
                    logger.info(f"Fallback: Kelas {oc.id} dijadwalkan dengan konflik {best_conflict}.")
                else:
                    logger.warning(f"Kelas {oc.id} gagal dijadwalkan, bahkan dengan fallback.")
        
        # Tambahkan solusi jadwal ini ke populasi
        population.append(solution)  # Kita simpan solusi ini di dalam populasi
        
    return population  # Kembalikan seluruh populasi jadwal

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
    penalties,
    db: Session,
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.1,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100,
):
    # Mulai hitung waktu komputasi
    start_time = datetime.now()
    
    clear_timetable(db)
    logger.info("Starting Hybrid GA-SA scheduling...")
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}
    recess_times = identify_recess_times(timeslot_cache)

    # ------------------------- GA Phase -------------------------
    population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times)
    for gen in range(generations):
        selected_pop = selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties, k=3)
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
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        )
        best_fitness_ga = fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        logger.info(f"GA Generation {gen+1}: Best fitness = {best_fitness_ga}")
        if best_fitness_ga == 0:
            logger.info("Optimal GA solution found; stopping GA early.")
            population = [best_solution_ga]
            break

    best_solution_ga = min(
        population,
        key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
    )
    logger.info(f"GA phase completed with best fitness = {fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)}")
    
    # ------------------------- SA Phase -------------------------
    current_solution = best_solution_ga
    current_fitness = fitness(current_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
    temperature = initial_temperature
    best_solution_sa = current_solution
    best_fitness_sa = current_fitness

    iteration = 0
    while temperature > 1:
        iteration += 1
        for i in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times)
            new_fitness = fitness(new_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
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
    
    # Hitung waktu komputasi total
    total_time = datetime.now() - start_time
    logger.info(f"Hybrid GA-SA scheduling completed with final best fitness = {best_fitness_sa}. Total computation time: {total_time}")
    
    # Hitung nilai fitness normalized untuk pelaporan:
    # Jika ada konflik, normalized_fitness = best_fitness_sa / conflict_multiplier; jika tidak, tetap best_fitness_sa.
    raw_conflict = check_conflicts(best_solution_sa, opened_class_cache, room_cache, timeslot_cache, penalties)
    if raw_conflict > 0:
        normalized_fitness = best_fitness_sa / penalties["conflict_multiplier"]
    else:
        normalized_fitness = best_fitness_sa
    logger.info(f"Normalized fitness (raw conflict score): {normalized_fitness}")

    # Kembalikan solusi beserta waktu komputasi dan nilai fitness normalized
    return {
        "timetable": formatted_solution,
        "computation_time": str(total_time),
        "final_fitness": normalized_fitness
    }

# =============================================================================
#                        HYBRID GA-SA ENDPOINT
# =============================================================================

@router.post("/generate-schedule-hybrid")
async def generate_schedule_hybrid(
    db: Session = Depends(get_db),
    population_size: int = 50,
    generations: int = 100,
    mutation_prob: float = 0.01,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100,
    # PENALTI
    room_conflict: int = Query(70, description="Penalty for room conflict"),
    lecturer_conflict: int = Query(50, description="Penalty for lecturer conflict"),
    cross_day: int = Query(500, description="Penalty for scheduling across multiple days"),
    invalid_timeslot: int = Query(500, description="Penalty for invalid timeslot"),
    wrong_room: int = Query(30, description="Penalty for wrong room assignment"),
    special_needs: int = Query(100, description="Penalty for special needs non-compliance"),
    daily_load: int = Query(500, description="Multiplier for daily load imbalance"),
    high_priority_preference: int = Query(50, description="Penalty for missing high-priority preference"),
    general_preference: int = Query(10, description="Penalty for missing general preference"),
    jabatan: int = Query(500, description="Penalty for jabatan constraint violation"),
    conflict_multiplier: int = Query(100, description="Multiplier for conflict penalties")
):
    try:
        penalties = {
            "room_conflict": room_conflict,
            "lecturer_conflict": lecturer_conflict,
            "cross_day": cross_day,
            "invalid_timeslot": invalid_timeslot,
            "wrong_room": wrong_room,
            "special_needs": special_needs,
            "daily_load": daily_load,
            "high_priority_preference": high_priority_preference,
            "general_preference": general_preference,
            "jabatan": jabatan,
            "conflict_multiplier": conflict_multiplier
        }

        best_timetable = hybrid_schedule(
            db=db,
            population_size=population_size,
            generations=generations,
            mutation_prob=mutation_prob,
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            iterations_per_temp=iterations_per_temp,
            penalties=penalties
        )
       
        return {
            "message": "Schedule generated successfully using Hybrid GA-SA",
            "computation_time": best_timetable["computation_time"],
            "final_fitness": best_timetable["final_fitness"]
        }
    except Exception as e:
        logger.error(f"Error generating schedule with Hybrid GA-SA: {e}")
        raise HTTPException(status_code=500, detail=str(e))



import matplotlib.pyplot as plt
import numpy as np
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

def hybrid_schedule_with_tracking(
    penalties,
    db: Session,
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.1,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100,
):
    # Mulai hitung waktu komputasi
    start_time = datetime.now()
    
    clear_timetable(db)
    logger.info("Memulai penjadwalan Hybrid GA-SA dengan pelacakan fitness...")
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}
    recess_times = identify_recess_times(timeslot_cache)

    # Lacak nilai fitness di setiap iterasi
    ga_fitness_history = []
    ga_avg_fitness_history = []
    sa_fitness_history = []
    
    # ------------------------- Fase GA -------------------------
    population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times)
    
    for gen in range(generations):
        # Hitung nilai fitness rata-rata populasi
        avg_fitness = sum(fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties) 
                          for sol in population) / len(population)
        ga_avg_fitness_history.append(avg_fitness)
        
        selected_pop = selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties, k=3)
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
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        )
        best_fitness_ga = fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        
        # Lacak fitness terbaik generasi ini
        ga_fitness_history.append(best_fitness_ga)
        
        logger.info(f"GA Generasi {gen+1}: Fitness terbaik = {best_fitness_ga}, Fitness rata-rata = {avg_fitness:.2f}")
        if best_fitness_ga == 0:
            logger.info("Solusi GA optimal ditemukan; menghentikan fase GA lebih awal.")
            population = [best_solution_ga]
            break

    best_solution_ga = min(
        population,
        key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
    )
    logger.info(f"Fase GA selesai dengan fitness terbaik = {fitness(best_solution_ga, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)}")
    
    # ------------------------- Fase SA -------------------------
    current_solution = best_solution_ga
    current_fitness = fitness(current_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
    temperature = initial_temperature
    best_solution_sa = current_solution
    best_fitness_sa = current_fitness

    # Tambahkan fitness awal sebelum iterasi SA
    sa_fitness_history.append(best_fitness_sa)
    
    iteration = 0
    while temperature > 1:
        iteration += 1
        iteration_best_fitness = best_fitness_sa  # Lacak fitness terbaik untuk level temperatur ini
        
        for i in range(iterations_per_temp):
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times)
            new_fitness = fitness(new_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
            
            # Kriteria penerimaan SA
            if new_fitness < current_fitness or random.random() < math.exp((current_fitness - new_fitness) / temperature):
                current_solution = new_solution
                current_fitness = new_fitness
                
                if current_fitness < best_fitness_sa:
                    best_solution_sa = current_solution
                    best_fitness_sa = current_fitness
                    iteration_best_fitness = best_fitness_sa
                    logger.info(f"SA Iterasi {iteration}.{i}: Fitness terbaik baru = {new_fitness}")
                    
                    if best_fitness_sa == 0:
                        temperature = 0
                        break
        
        # Tambahkan fitness terbaik level temperatur ini ke histori
        sa_fitness_history.append(iteration_best_fitness)
        
        if best_fitness_sa == 0:
            break
            
        temperature *= cooling_rate
        logger.info(f"SA Pendinginan: Temperatur sekarang = {temperature:.2f}")

    # ------------------------- Finalisasi -------------------------
    formatted_solution = format_solution_for_db(db, best_solution_sa, opened_class_cache, room_cache, timeslot_cache)
    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)
    
    # Hitung waktu komputasi total
    total_time = datetime.now() - start_time
    logger.info(f"Penjadwalan Hybrid GA-SA selesai dengan fitness akhir terbaik = {best_fitness_sa}. Total waktu komputasi: {total_time}")
    
    # Hitung nilai fitness normalized untuk pelaporan
    raw_conflict = check_conflicts(best_solution_sa, opened_class_cache, room_cache, timeslot_cache, penalties)
    if raw_conflict > 0:
        normalized_fitness = best_fitness_sa / penalties["conflict_multiplier"]
    else:
        normalized_fitness = best_fitness_sa
    logger.info(f"Fitness normalisasi (skor konflik mentah): {normalized_fitness}")

    # Plot histori fitness
    plot_fitness_evolution(ga_fitness_history, ga_avg_fitness_history, sa_fitness_history)
    
    # Kembalikan solusi beserta waktu komputasi, nilai fitness normalized, dan histori fitness
    return {
        "timetable": formatted_solution,
        "computation_time": str(total_time),
        "final_fitness": normalized_fitness,
        "ga_fitness_history": ga_fitness_history,
        "ga_avg_fitness_history": ga_avg_fitness_history,
        "sa_fitness_history": sa_fitness_history
    }

def plot_fitness_history(ga_fitness_history, ga_avg_fitness_history, sa_fitness_history):
    """
    Membuat dan menyimpan plot yang menunjukkan peningkatan fitness selama iterasi 
    untuk fase GA dan SA, dengan label dalam Bahasa Indonesia.
    """
    plt.figure(figsize=(12, 8))
    plt.style.use('ggplot')  # Gunakan style yang lebih modern
    
    # Plot untuk fase GA dengan nilai terbaik dan rata-rata
    plt.subplot(2, 1, 1)
    x_ga = range(1, len(ga_fitness_history) + 1)
    plt.plot(x_ga, ga_fitness_history, marker='o', markersize=4, linestyle='-', linewidth=2, 
             color='#1f77b4', label='Fitness Terbaik')
    plt.plot(x_ga, ga_avg_fitness_history, marker='s', markersize=3, linestyle='-', linewidth=1.5, 
             color='#ff7f0e', label='Fitness Rata-rata')
    plt.title('Perkembangan Fitness Algoritma Genetika', fontsize=14, fontweight='bold')
    plt.xlabel('Generasi', fontsize=12)
    plt.ylabel('Nilai Fitness (semakin rendah semakin baik)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True)
    
    # Plot untuk fase SA
    plt.subplot(2, 1, 2)
    x_sa = range(1, len(sa_fitness_history) + 1)
    plt.plot(x_sa, sa_fitness_history, marker='o', markersize=4, linestyle='-', linewidth=2, 
             color='#d62728', label='Fitness Terbaik')
    plt.title('Perkembangan Fitness Simulated Annealing', fontsize=14, fontweight='bold')
    plt.xlabel('Level Temperatur', fontsize=12)
    plt.ylabel('Nilai Fitness (semakin rendah semakin baik)', fontsize=12)
    plt.legend(fontsize=10)
    plt.grid(True)
    
    plt.tight_layout(pad=3.0)
    plt.savefig('fitness_history_ga_sa.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Buat plot kombinasi dengan skala logaritmik
    plt.figure(figsize=(14, 10))
    
    # Gabungkan kedua histori
    combined_history = ga_fitness_history + sa_fitness_history[1:]  # Hindari duplikasi nilai transisi
    combined_x = list(range(1, len(combined_history) + 1))
    
    # Plot dengan skala logaritmik jika rentang datanya cukup besar
    if max(combined_history) / (min(combined_history) + 0.1) > 10:  # Tambahkan 0.1 untuk menghindari pembagian dengan nol
        plt.semilogy(combined_x, combined_history, marker='o', markersize=5, linestyle='-', 
                    linewidth=2, color='#2ca02c', label='Nilai Fitness')
    else:
        plt.plot(combined_x, combined_history, marker='o', markersize=5, linestyle='-', 
                linewidth=2, color='#2ca02c', label='Nilai Fitness')
    
    # Tambahkan garis vertikal untuk menandai transisi dari GA ke SA
    plt.axvline(x=len(ga_fitness_history), color='red', linestyle='--', linewidth=2, 
               label='Transisi GA ke SA')
    
    # Anotasi untuk menjelaskan bagian GA dan SA
    plt.annotate('Fase GA', xy=(len(ga_fitness_history)/2, plt.ylim()[1]*0.9),
                xytext=(len(ga_fitness_history)/2, plt.ylim()[1]*0.9),
                ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.annotate('Fase SA', xy=(len(ga_fitness_history) + len(sa_fitness_history[1:])/2, plt.ylim()[1]*0.9),
                xytext=(len(ga_fitness_history) + len(sa_fitness_history[1:])/2, plt.ylim()[1]*0.9),
                ha='center', va='center', fontsize=12, fontweight='bold')
    
    plt.title('Evolusi Fitness Keseluruhan Algoritma Hybrid GA-SA', fontsize=16, fontweight='bold')
    plt.xlabel('Iterasi', fontsize=14)
    plt.ylabel('Nilai Fitness (semakin rendah semakin baik)', fontsize=14)
    plt.legend(fontsize=12, loc='upper right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('evolusi_fitness_keseluruhan.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Buat diagram perbandingan fitness awal dan akhir
    plt.figure(figsize=(10, 6))
    
    # Data untuk diagram batang
    labels = ['Awal GA', 'Akhir GA / Awal SA', 'Akhir SA']
    values = [ga_fitness_history[0], ga_fitness_history[-1], sa_fitness_history[-1]]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    bars = plt.bar(labels, values, color=colors, width=0.6)
    
    # Tambahkan nilai di atas batang
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1*max(values),
                f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.title('Perbandingan Nilai Fitness di Berbagai Tahap Algoritma', fontsize=16, fontweight='bold')
    plt.ylabel('Nilai Fitness (semakin rendah semakin baik)', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Menambahkan persentase perbaikan
    improvement_ga = ((ga_fitness_history[0] - ga_fitness_history[-1]) / ga_fitness_history[0]) * 100
    improvement_sa = ((ga_fitness_history[-1] - sa_fitness_history[-1]) / ga_fitness_history[-1]) * 100
    improvement_total = ((ga_fitness_history[0] - sa_fitness_history[-1]) / ga_fitness_history[0]) * 100
    
    plt.figtext(0.15, 0.01, f"Perbaikan GA: {improvement_ga:.1f}%", fontsize=11)
    plt.figtext(0.5, 0.01, f"Perbaikan SA: {improvement_sa:.1f}%", fontsize=11)
    plt.figtext(0.85, 0.01, f"Perbaikan Total: {improvement_total:.1f}%", fontsize=11)
    
    plt.tight_layout(pad=4.0)
    plt.savefig('perbandingan_fitness.png', dpi=300, bbox_inches='tight')
    plt.close()
    
def plot_fitness_evolution(ga_fitness_history, ga_avg_fitness_history, sa_fitness_history):
    """
    Membuat grafik garis yang menampilkan evolusi fitness terbaik dan rata-rata
    selama iterasi algoritma hybrid GA-SA dengan label nilai setiap 25 iterasi.
    Termasuk nilai rata-rata fitness untuk kedua fase GA dan SA.
    """
    # Menggabungkan fitness terbaik dari kedua fase (hindari duplikasi di transisi)
    full_best_fitness = ga_fitness_history + sa_fitness_history[1:]
    
    # Buat array x untuk fitness terbaik
    full_iterations_best = list(range(1, len(full_best_fitness) + 1))
    
    # Buat array x untuk fitness rata-rata GA
    iterations_ga_avg = list(range(1, len(ga_avg_fitness_history) + 1))
    
    # Buat data rata-rata untuk SA (karena tidak ada populasi di SA, 
    # kita bisa menghitung rata-rata bergerak dari fitness terbaik)
    sa_avg_fitness_history = []
    window_size = 3  # Ukuran jendela untuk rata-rata bergerak
    
    # Kita bisa menggunakan rata-rata bergerak sederhana
    for i in range(1, len(sa_fitness_history)):
        start_idx = max(0, i - window_size)
        window = sa_fitness_history[start_idx:i+1]
        avg = sum(window) / len(window)
        sa_avg_fitness_history.append(avg)
    
    # Buat array x untuk fitness rata-rata SA
    iterations_sa_avg = list(range(len(ga_fitness_history) + 1, 
                                   len(ga_fitness_history) + len(sa_avg_fitness_history) + 1))
    
    # Membuat figure dengan ukuran yang tepat
    plt.figure(figsize=(15, 8))
    
    # Plot garis untuk fitness terbaik dengan warna biru
    plt.plot(full_iterations_best, full_best_fitness, 'b-', linewidth=2, marker='o', 
             markersize=3, label='Fitness Terbaik')
    
    # Plot garis untuk fitness rata-rata GA dengan warna oranye
    plt.plot(iterations_ga_avg, ga_avg_fitness_history, 'orange', 
             linewidth=1.5, marker='^', markersize=3, label='Fitness Rata-rata (GA)')
    
    # Plot garis untuk fitness rata-rata SA dengan warna hijau
    plt.plot(iterations_sa_avg, sa_avg_fitness_history, 'green', 
             linewidth=1.5, marker='s', markersize=3, label='Fitness Rata-rata (SA)')
    
    # Tambahkan garis vertikal untuk menandai transisi dari GA ke SA
    plt.axvline(x=len(ga_fitness_history), color='r', linestyle='--', linewidth=2,
                label='Transisi GA ke SA')
    
    # Tambahkan label nilai fitness setiap 25 iterasi
    label_interval = 25
    for i in range(0, len(full_best_fitness), label_interval):
        if i < len(full_best_fitness):
            plt.annotate(f"{int(full_best_fitness[i])}", 
                        xy=(full_iterations_best[i], full_best_fitness[i]),
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', va='bottom',
                        fontsize=9, color='blue')
    
    # Tambahkan label nilai fitness rata-rata setiap 25 iterasi untuk fase GA
    for i in range(0, len(ga_avg_fitness_history), label_interval):
        if i < len(ga_avg_fitness_history):
            plt.annotate(f"{int(ga_avg_fitness_history[i])}", 
                        xy=(iterations_ga_avg[i], ga_avg_fitness_history[i]),
                        xytext=(0, -15), textcoords='offset points',
                        ha='center', va='top',
                        fontsize=9, color='darkorange')
    
    # Tambahkan label nilai fitness rata-rata setiap 25 iterasi untuk fase SA
    sa_label_indices = [i for i in range(0, len(sa_avg_fitness_history), label_interval)]
    if len(sa_avg_fitness_history) > 0 and sa_label_indices:
        for i in sa_label_indices:
            if i < len(sa_avg_fitness_history):
                idx = iterations_sa_avg[i] - 1  # Sesuaikan indeks
                plt.annotate(f"{int(sa_avg_fitness_history[i])}", 
                            xy=(iterations_sa_avg[i], sa_avg_fitness_history[i]),
                            xytext=(0, -15), textcoords='offset points',
                            ha='center', va='top',
                            fontsize=9, color='darkgreen')
    
    # Konfigurasi grafik
    plt.title('Evolusi Fitness Selama Iterasi Algoritma Hybrid', fontsize=16, fontweight='bold')
    plt.xlabel('Iterasi', fontsize=14)
    plt.ylabel('Nilai Fitness (semakin rendah semakin baik)', fontsize=14)
    
    # Tambahkan grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Atur Y-axis limits untuk memastikan label terlihat
    plt.ylim(bottom=0)
    
    # Tambahkan legenda
    plt.legend(loc='upper right', fontsize=12)
    
    # Tambahkan anotasi fase
    ymin, ymax = plt.ylim()
    plt.text(len(ga_fitness_history)/2, ymax*0.9, 'Fase GA', 
             ha='center', fontsize=14, fontweight='bold')
    plt.text(len(ga_fitness_history) + len(sa_fitness_history[1:])/2, 
             ymax*0.9, 'Fase SA', ha='center', fontsize=14, fontweight='bold')
    
    # Mengatur tampilan dan menyimpan grafik
    plt.tight_layout()
    plt.savefig('fitness_evolution_with_labels.png', dpi=300, bbox_inches='tight')
    
    # Buat versi dengan skala logaritmik jika nilai fitness sangat bervariasi
    plt.figure(figsize=(15, 8))
    plt.semilogy(full_iterations_best, full_best_fitness, 'b-', linewidth=2, marker='o', 
                markersize=3, label='Fitness Terbaik')
    plt.semilogy(iterations_ga_avg, ga_avg_fitness_history, 'orange', 
                linewidth=1.5, marker='^', markersize=3, label='Fitness Rata-rata (GA)')
    
    # Tambahkan rata-rata SA ke versi log juga
    if len(sa_avg_fitness_history) > 0:
        plt.semilogy(iterations_sa_avg, sa_avg_fitness_history, 'green', 
                    linewidth=1.5, marker='s', markersize=3, label='Fitness Rata-rata (SA)')
    
    plt.axvline(x=len(ga_fitness_history), color='r', linestyle='--', linewidth=2,
                label='Transisi GA ke SA')
    
    # Tambahkan label nilai fitness setiap 25 iterasi pada skala logaritmik
    for i in range(0, len(full_best_fitness), label_interval):
        if i < len(full_best_fitness):
            plt.annotate(f"{int(full_best_fitness[i])}", 
                        xy=(full_iterations_best[i], full_best_fitness[i]),
                        xytext=(0, 10), textcoords='offset points',
                        ha='center', va='bottom',
                        fontsize=9, color='blue')
    
    plt.title('Evolusi Fitness Selama Iterasi Algoritma Hybrid (Skala Log)', fontsize=16, fontweight='bold')
    plt.xlabel('Iterasi', fontsize=14)
    plt.ylabel('Nilai Fitness (Log, semakin rendah semakin baik)', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='upper right', fontsize=12)
    
    ymin, ymax = plt.ylim()
    plt.text(len(ga_fitness_history)/2, ymax*0.5, 'Fase GA', 
             ha='center', fontsize=14, fontweight='bold')
    plt.text(len(ga_fitness_history) + len(sa_fitness_history[1:])/2, 
             ymax*0.5, 'Fase SA', ha='center', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('fitness_evolution_log_scale_with_labels.png', dpi=300, bbox_inches='tight')
    
    return plt
@router.post("/generate-schedule-hybrid-with-tracking")
async def generate_schedule_hybrid_with_tracking(
    db: Session = Depends(get_db),
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.10,
    initial_temperature: float = 1500,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100,
    # PENALTI
    room_conflict: int = Query(70, description="Penalty for room conflict"),
    lecturer_conflict: int = Query(50, description="Penalty for lecturer conflict"),
    cross_day: int = Query(500, description="Penalty for scheduling across multiple days"),
    invalid_timeslot: int = Query(500, description="Penalty for invalid timeslot"),
    wrong_room: int = Query(30, description="Penalty for wrong room assignment"),
    special_needs: int = Query(100, description="Penalty for special needs non-compliance"),
    daily_load: int = Query(500, description="Multiplier for daily load imbalance"),
    high_priority_preference: int = Query(50, description="Penalty for missing high-priority preference"),
    general_preference: int = Query(10, description="Penalty for missing general preference"),
    jabatan: int = Query(500, description="Penalty for jabatan constraint violation"),
    conflict_multiplier: int = Query(100, description="Multiplier for conflict penalties")
):
    try:
        penalties = {
            "room_conflict": room_conflict,
            "lecturer_conflict": lecturer_conflict,
            "cross_day": cross_day,
            "invalid_timeslot": invalid_timeslot,
            "wrong_room": wrong_room,
            "special_needs": special_needs,
            "daily_load": daily_load,
            "high_priority_preference": high_priority_preference,
            "general_preference": general_preference,
            "jabatan": jabatan,
            "conflict_multiplier": conflict_multiplier
        }

        result = hybrid_schedule_with_tracking(
            db=db,
            population_size=population_size,
            generations=generations,
            mutation_prob=mutation_prob,
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            iterations_per_temp=iterations_per_temp,
            penalties=penalties
        )
       
        return {
            "message": "Jadwal berhasil dibuat menggunakan Hybrid GA-SA dengan pelacakan fitness",
            "computation_time": result["computation_time"],
            "final_fitness": result["final_fitness"],
            "fitness_history_graphs": "Grafik dihasilkan dan disimpan sebagai file PNG",
            "ga_fitness_history": result["ga_fitness_history"],
            "ga_avg_fitness_history": result["ga_avg_fitness_history"],
            "sa_fitness_history": result["sa_fitness_history"]
        }
    except Exception as e:
        logger.error(f"Error membuat jadwal dengan Hybrid GA-SA tracking: {e}")
        raise HTTPException(status_code=500, detail=str(e))