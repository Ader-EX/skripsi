from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import random
import logging
import math

from database import get_db
from routes.algorithm_routes import clear_timetable, fetch_data
from model.academicperiod_model import AcademicPeriods
from model.ruangan_model import Ruangan
from model.timeslot_model import TimeSlot
from model.preference_model import Preference
from model.openedclass_model import OpenedClass
from model.timetable_model import TimeTable
from model.openedclass_model import openedclass_dosen

router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------
# -------------------- CONSTRAINT & FITNESS FUNCTIONS --------------------
# ------------------------------------------------------------------------


def debug_fitness_components(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache):
    """
    Returns a breakdown of each fitness component for the given solution.
    """
    # Check conflicts first – if there is any conflict, the fitness function multiplies it by 1000.
    conflict = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache)
    conflict_total = conflict * 1000 if conflict > 0 else 0

    room_type = check_room_type_compatibility(solution, opened_class_cache, room_cache)
    special_needs = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache)
    preference = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache)
    jabatan = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache)

    total = conflict_total + room_type + special_needs + preference + jabatan
    return {
        "conflict": conflict,
        "conflict_total": conflict_total,
        "room_type_score": room_type,
        "special_needs_score": special_needs,
        "preference_score": preference,
        "jabatan_penalty": jabatan,
        "total": total
    }


def check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache):
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



def get_effective_sks(class_info):
    """Return effective SKS: if the class type is 'P' (practical), multiply by 2."""
    sks = class_info['sks']
    if class_info['mata_kuliah'].tipe_mk == 'P':
        return sks * 2
    return sks

from datetime import datetime
def identify_recess_times(timeslot_cache):
    """Identify timeslot IDs that start after a gap longer than 10 minutes."""
    recess_times = set()
    sorted_slots = sorted(timeslot_cache.values(), key=lambda x: (x.day_index, x.start_time))
    for i in range(len(sorted_slots) - 1):
        current_slot = sorted_slots[i]
        next_slot = sorted_slots[i + 1]
        current_end = datetime.combine(datetime.today(), current_slot.end_time)
        next_start = datetime.combine(datetime.today(), next_slot.start_time)
        if (next_start - current_end).total_seconds() > 600:  # gap > 10 minutes
            recess_times.add(next_slot.id)
    return recess_times


def check_room_type_compatibility(solution, opened_class_cache, room_cache):
    """
    Pastikan mata kuliah Praktikum di ruangan Praktikum, dan Teori di ruangan Teori.
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        mk = class_info['mata_kuliah']
        room = room_cache[room_id]

        if mk.tipe_mk == 'P' and room.tipe_ruangan != 'P':
            penalty += 1000  
        elif mk.tipe_mk == 'T' and room.tipe_ruangan != 'T':
            penalty += 1000  
    return penalty

def check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache):
    """
    Dosen dengan kebutuhan khusus harus di ruangan 'KHD2' atau 'DS2'.
    """
    penalty = 0
    for opened_class_id, room_id, _ in solution:
        class_info = opened_class_cache[opened_class_id]
        room = room_cache[room_id]

        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            # Jika dosen ini is_special_needs, pastikan group_code ruangan sesuai
            if dosen_key in preferences_cache and preferences_cache[dosen_key].get('is_special_needs', False):
                if room.group_code not in ['KHD2', 'DS2']:
                    penalty += 1000
    return penalty

def check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache):
    """
    Penalti jika preferensi dosen tidak diikuti.
    """
    penalty = 0
    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        for dosen_id in class_info['dosen_ids']:
            dosen_key = (opened_class_id, dosen_id)
            if dosen_key in preferences_cache:
                pref_info = preferences_cache[dosen_key]
                # is_high_priority = dosen TIDAK BISA mengajar di slot ini
                if pref_info.get('is_high_priority', False):
                    if timeslot_id in pref_info['preferences']:
                        penalty += 800
                # used_preference = preferensi normal
                elif pref_info.get('used_preference', False):
                    if timeslot_id not in pref_info['preferences']:
                        penalty += 200
    return penalty

def check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache):
    """
    Memastikan bahwa jika dosen memiliki jabatan (non-null), 
    mereka tidak dijadwalkan pada hari Senin (day_index == 0).
    Setiap pelanggaran mendapatkan penalti besar.
    """
    penalty = 0
    for opened_class_id, room_id, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        timeslot = timeslot_cache[timeslot_id]
        # Jika timeslot berada di Senin (day_index == 0)
        if timeslot.day_index == 0:
            for dosen_id in class_info["dosen_ids"]:
                dosen = dosen_cache.get(dosen_id)
                if dosen and dosen.jabatan is not None:
                    penalty += 10000
    return penalty

def fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache):
    """
    Hitung total penalti (semakin kecil semakin baik).
    Jika ada konflik, langsung kembalikan penalti besar.
    """
    conflict_score = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache)
    if conflict_score > 0:
        return conflict_score * 1000  # Konversi ke penalti besar

    room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache)
    special_needs_score = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache)
    preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache)
    jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache)

    total = room_type_score + special_needs_score + preference_score + jabatan_penalty
    return total

# ------------------------------------------------------------------------
# --------------------- GA SUPPORT FUNCTIONS -----------------------------
# ------------------------------------------------------------------------

def selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, k=3):
    """
    Tournament selection: pilih individu terbaik dari k calon secara acak.
    """
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
    """
    Menggabungkan dua solusi (parent) menjadi dua solusi (child).
    Sederhana: one-point crossover.
    """
    if len(parent1) == 0 or len(parent2) == 0:
        return parent1, parent2  # Tidak ada crossover jika salah satu parent kosong

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
                    logger.info(f"🔄 Mutasi: Kelas {opened_class_id} dipindah ke Ruang {new_room.id}, Timeslot {slots[0].id}")
                    break

    return new_solution

# ------------------------------------------------------------------------
# ---------------- DATA PREPARATION & SOLUTION INITIALIZATION ------------
# ------------------------------------------------------------------------

def fetch_dosen_preferences(db: Session, opened_classes: List[OpenedClass]):
    """
    Mengambil preferensi dosen dari tabel Preference, dikaitkan dengan each opened_class.
    """
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

def initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times):
    population = []
    # Sort timeslots as before
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))

    for _ in range(population_size):
        solution = []
        room_schedule = {}
        lecturer_schedule = {}
        # Sort classes in descending order of effective SKS
        sorted_classes = sorted(
            opened_classes, key=lambda oc: get_effective_sks(opened_class_cache[oc.id]), reverse=True
        )

        for oc in sorted_classes:
            class_info = opened_class_cache[oc.id]
            effective_sks = get_effective_sks(class_info)
            tipe_mk = class_info["mata_kuliah"].tipe_mk

            compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
            if not compatible_rooms:
                logger.warning(f"No available room for {oc.id} ({tipe_mk})")
                continue

            assigned = False
            random.shuffle(compatible_rooms)
            possible_start_idxs = list(range(len(timeslots_list) - effective_sks + 1))
            random.shuffle(possible_start_idxs)

            for room in compatible_rooms:
                if assigned:
                    break

                for start_idx in possible_start_idxs:
                    slots = timeslots_list[start_idx : start_idx + effective_sks]
                    # Check consecutive timeslots and avoid recess times
                    if not all(
                        slots[i].day_index == slots[0].day_index and 
                        slots[i].id == slots[i-1].id + 1 and
                        slots[i].id not in recess_times
                        for i in range(1, effective_sks)
                    ):
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
            if not assigned:
                logger.warning(f"Could not assign class {oc.id} in initial population; using fallback random assignment.")
                # Pick a random room from the compatible ones
                fallback_room = random.choice(compatible_rooms)
                # Pick a random index for timeslot block that can accommodate effective_sks (ignoring consecutive constraint)
                fallback_start_idx = random.randint(0, len(timeslots_list) - effective_sks)
                fallback_slots = timeslots_list[fallback_start_idx : fallback_start_idx + effective_sks]
                # Note: this fallback might violate consecutive or recess constraints.
                solution.append((oc.id, fallback_room.id, fallback_slots[0].id))
            # if not assigned:
            #     logger.warning(f"Could not assign class {oc.id} in initial population")

        population.append(solution)
    return population

# ------------------------------------------------------------------------
# ---------------- FORMAT & INSERT INTO DATABASE FUNCTIONS --------------
# ------------------------------------------------------------------------

def format_solution_for_db(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    """
    Ubah solution (list of (class, room, timeslot)) menjadi list dict TimeTable.
    """
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found.")

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

def insert_timetable(db: Session, timetable: List[Dict], opened_class_cache: Dict, room_cache: Dict, timeslot_cache: Dict):
    """
    Masukkan jadwal final ke database (TimeTable).
    """
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("No active academic period found.")

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

# ------------------------------------------------------------------------
# ------------------ GENETIC ALGORITHM IMPLEMENTATION --------------------
# ------------------------------------------------------------------------

def genetic_algorithm(db: Session, population_size=50, generations=50, mutation_prob=0.1):
    """
    Genetic Algorithm untuk penjadwalan:
      1. Bersihkan jadwal lama.
      2. Ambil data (mata kuliah, ruangan, timeslot, dsb).
      3. Inisialisasi populasi.
      4. Loop evolusi (generations):
         - selection
         - crossover
         - mutate
         - evaluasi fitness
         - Jika ditemukan solusi dengan fitness 0, berhenti lebih awal.
      5. Pilih solusi terbaik, format, dan simpan.
    """
    # 1. Hapus jadwal lama
    clear_timetable(db)
    logger.info("🔥 Memulai Genetic Algorithm untuk penjadwalan...")

    # 2. Ambil data
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    recess_times = identify_recess_times(timeslot_cache)
    # Buat dosen_cache untuk pengecekan jabatan (menggunakan pegawai_id sebagai key)
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}

    # 3. Buat populasi awal
    population = initialize_population(opened_classes, rooms, timeslots, population_size, opened_class_cache, recess_times)

    # 4. Loop evolusi
    for gen in range(generations):
        # 4a. Selection
        selected_pop = selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, k=3)

        # 4b. Crossover
        new_population = []
        for i in range(0, len(selected_pop), 2):
            if i + 1 < len(selected_pop):
                parent1 = selected_pop[i]
                parent2 = selected_pop[i+1]
                child1, child2 = crossover(parent1, parent2)
                new_population.extend([child1, child2])
            else:
                new_population.append(selected_pop[i])

        # 4c. Mutation
        mutated_population = []
        for indiv in new_population:
            mutated_indiv = mutate(indiv, opened_classes, rooms, timeslots, opened_class_cache, recess_times, mutation_prob)
            mutated_population.append(mutated_indiv)

        # Ganti populasi dengan hasil baru
        population = mutated_population

        # Evaluasi fitness terbaik generasi ini
        best_solution = min(
            population,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
        )
        best_fitness = fitness(best_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
        logger.info(f"🌀 Generasi {gen+1}: Fitness terbaik = {best_fitness}")


        if best_fitness == 2000:
            debug_info = debug_fitness_components(best_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
            logger.info(f"🛠 Debug info for solution at fitness 2000: {debug_info}")

        # Early stopping jika solusi optimal ditemukan (fitness == 0)
        if best_fitness == 0:
            logger.info("🏆 Solusi optimal ditemukan dengan fitness 0. Menghentikan evolusi lebih awal.")
            population = [best_solution]
            break

    # 5. Pilih solusi terbaik dari populasi akhir
    final_best = min(
        population,
        key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)
    )
    final_score = fitness(final_best, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache)

    # Format dan masukkan ke DB
    formatted_solution = format_solution_for_db(db, final_best, opened_class_cache, room_cache, timeslot_cache)
    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)

    logger.info(f"🎯 GA Selesai! Skor Akhir Terbaik = {final_score}")
    return formatted_solution

# ------------------------------------------------------------------------
# -------------------------- FASTAPI ROUTE -------------------------------
# ------------------------------------------------------------------------

@router.post("/generate-schedule-ga")
async def generate_schedule_ga(
    db: Session = Depends(get_db),
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.1
):
    """
    Endpoint untuk menjalankan Genetic Algorithm scheduling.
    - population_size: Jumlah individu dalam populasi
    - generations: Berapa banyak iterasi generasi
    - mutation_prob: Peluang terjadinya mutasi
    """
    try:
        logger.info("Generating schedule using Genetic Algorithm...")
        best_timetable = genetic_algorithm(
            db=db,
            population_size=population_size,
            generations=generations,
            mutation_prob=mutation_prob
        )
        return {
            "message": "Schedule generated successfully using Genetic Algorithm",
            "best_timetable": best_timetable
        }
    except Exception as e:
        logger.error(f"Error generating schedule with GA: {e}")
        raise HTTPException(status_code=500, detail=str(e))
