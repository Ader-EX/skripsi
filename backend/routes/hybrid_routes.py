
import math
import random
import logging

from datetime import datetime
from typing import  Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from routes.sa_routes import get_effective_sks, identify_recess_times
from database import get_db
from routes.algorithm_routes import clear_timetable, fetch_data
from model.academicperiod_model import AcademicPeriods

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
                    conflicts += penalties["room_conflict"]  # Penalti ruangan bentrok
            timeslot_usage[current_id].append((room_id, opened_class_id))

            for dosen_id in class_info['dosen_ids']:
                schedule_key = (dosen_id, current_id)
                if schedule_key in lecturer_schedule:
                    conflicts += penalties["lecturer_conflict"]  # Penalti  dosen bentrok
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

    # loop semua jadwal
    for opened_class_id, _, timeslot_id in solution:
        class_info = opened_class_cache[opened_class_id]
        for dosen_id in class_info['dosen_ids']:
            day = timeslot_cache[timeslot_id].day
            # bikin mapping dosen -> hari -> jumlah ngajar
            if dosen_id not in lecturer_daily_counts:
                lecturer_daily_counts[dosen_id] = {}
            if day not in lecturer_daily_counts[dosen_id]:
                lecturer_daily_counts[dosen_id][day] = 0
            lecturer_daily_counts[dosen_id][day] += 1

    # cek balance per dosen
    for dosen_id, day_counts in lecturer_daily_counts.items():
        counts = list(day_counts.values())
        if not counts:
            continue
        avg = sum(counts) / len(counts)  # hitung rata-rata ngajar per hari
        for count in counts:
            # kalau beda jauh bgt sama rata-rata (selisih > 4) kena penalti
            if abs(count - avg) > 4:
                penalty += penalties["daily_load"] * abs(count - avg)

    return penalty


def check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache, penalties):
    penalty = 0

    for opened_class_id, _, timeslot_id in solution:
        for dosen_id in opened_class_cache[opened_class_id]['dosen_ids']:
            key = (opened_class_id, dosen_id)
            if key not in preferences_cache:
                continue
            pref_info = preferences_cache[key]

            # high-priority -> forbidden
            if pref_info['is_high_priority']:
                if timeslot_id in pref_info['preferences']:
                    penalty += penalties['high_priority_preference']
            # low priority -> general preference
            elif pref_info['used_preference']:
                if timeslot_id not in pref_info['preferences']:
                    penalty += penalties['general_preference']

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
    
    room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache, penalties)
    special_needs_score = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache, penalties)
    daily_load_score = check_daily_load_balance(solution, opened_class_cache, timeslot_cache, penalties)
    preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache, penalties)
    jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache, penalties)
    
    soft_score = room_type_score + special_needs_score + daily_load_score + preference_score + jabatan_penalty
    
   
    if conflict_score > 0:
        return (conflict_score * penalties["conflict_multiplier"]) + soft_score
    else:
        return soft_score
def generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times):
    # clone dulu solusi sekarang biar originalnya aman
    new_solution = current_solution.copy()
    if not new_solution:
        return new_solution

    # pilih random satu kelas buat dimutasi
    idx = random.randrange(len(new_solution))
    opened_class_id, _, _ = new_solution[idx]
    class_info = opened_class_cache[opened_class_id]
    tipe_mk = class_info["mata_kuliah"].tipe_mk

    # cari ruangan yang kompatibel (tipe ruangan sama tipe mata kuliah)
    compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
    if not compatible_rooms:
        return new_solution

    # acak pilih ruangan baru buat kelas ini
    new_room = random.choice(compatible_rooms)
    effective_sks = get_effective_sks(class_info)

    # semua kemungkinan start index timeslot
    possible_indices = list(range(len(timeslots)))
    random.shuffle(possible_indices)

    # cari potongan timeslot yang valid
    for start_idx in possible_indices:
        if start_idx + effective_sks > len(timeslots):
            continue
        slots = timeslots[start_idx: start_idx + effective_sks]

        # cek syarat:
        # - semua slot masih di hari yg sama
        # - ID berurutan
        # - jam start-end nyambung
        # - bukan jam istirahat
        if all(
            slots[i].day_index == slots[0].day_index and 
            slots[i].id == slots[i - 1].id + 1 and 
            slots[i].start_time == slots[i - 1].end_time and 
            slots[i].id not in recess_times
            for i in range(1, effective_sks)
        ):
            # kalau ketemu, langsung ganti entri yang dipilih
            new_solution[idx] = (opened_class_id, new_room.id, slots[0].id)
            break

    return new_solution  # balikin solusi baru hasil neighbor


def format_solution_for_db(db: Session, solution, opened_class_cache, room_cache, timeslot_cache):
    active_period = db.query(AcademicPeriods).filter(AcademicPeriods.is_active == True).first()
    if not active_period:
        raise ValueError("Active academic period tidak ditemukan")
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
                    raise ValueError(f"Timeslots memiliki hari yang berbeda {opened_class_id}")
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
        raise ValueError("Active academic period tidak ditemukan")
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

def selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties, k=3):
    selected = []
    for _ in range(len(population)):
        candidates = random.sample(population, k)
        best_candidate = min(
            candidates,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        )
        selected.append(best_candidate)
    return selected

def roulette_wheel_selection(population, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties):
    fitness_values = [1 / (1 + fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties))
                      for sol in population]
    total_fitness = sum(fitness_values)
    probabilities = [f / total_fitness for f in fitness_values]
    selected = random.choices(population, weights=probabilities, k=len(population))
    return selected

def crossover(parent1, parent2):
    if len(parent1) == 0 or len(parent2) == 0:
        return parent1, parent2
    point = random.randint(1, min(len(parent1), len(parent2)) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

def mutate(solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times, preferences_cache, mutation_prob=0.1):
    new_solution = solution.copy()
    if not new_solution:
        return new_solution
    if random.random() < mutation_prob:
        # ngambil salah satu entri solusi
        idx = random.randrange(len(new_solution))

        opened_class_id, _, _ = new_solution[idx]
        class_info = opened_class_cache[opened_class_id]
        effective_sks = get_effective_sks(class_info)
        tipe_mk = class_info["mata_kuliah"].tipe_mk
        compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]

        if compatible_rooms:
            new_room = random.choice(compatible_rooms)
            valid_timeslots = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))
            # [0,1,2,3,…] artinya potongan 2-slot bisa mulai di index 0,1,2,…
            possible_indices = list(range(len(valid_timeslots) - effective_sks + 1))
            
            random.shuffle(possible_indices)

            # pisahin timeslot berdasarkan preferensi dosen
            preferred_timeslots = []
            non_preferred_timeslots = []

            # buat nyari timeslot yang possible aja
            for start_idx in possible_indices:
                slots = valid_timeslots[start_idx : start_idx + effective_sks]
                slot_ids = {slot.id for slot in slots}

                is_preferred = all(
                    any(t in preferences_cache.get((opened_class_id, dosen_id), {}).get('preferences', {}) for t in slot_ids)
                    for dosen_id in class_info["dosen_ids"]
                )

                if is_preferred:
                    preferred_timeslots.append(start_idx)
                else:
                    non_preferred_timeslots.append(start_idx)

            sorted_indices = preferred_timeslots + non_preferred_timeslots

            # diurutin, trus buat dicari dia nyambung engganya
            for start_idx in sorted_indices:
                # ngambil potongan sebanyak sks 
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

def initialize_population(
    opened_classes, rooms, timeslots, population_size,
    opened_class_cache, recess_times, preferences_cache, dosen_cache
):
 
    population = []
    timeslots_list = sorted(timeslots, key=lambda x: (x.day_index, x.start_time))
    
    for _ in range(population_size):
       
        solution = []
        room_schedule = {}      # Menyimpan jadwal penggunaan ruangan dengan format (room_id, slot_id) -> kelas_id
        lecturer_schedule = {}  # Menyimpan jadwal dosen dengan format (dosen_id, slot_id) -> kelas_id
        
        
        sorted_classes = sorted(
            opened_classes,
            key=lambda oc: get_effective_sks(opened_class_cache[oc.id]),
            reverse=True
        )
        
        for oc in sorted_classes:
            class_info = opened_class_cache[oc.id]
            sks = get_effective_sks(class_info)
            tipe_mk = class_info["mata_kuliah"].tipe_mk

          
            compatible_rooms = [r for r in rooms if r.tipe_ruangan == tipe_mk]
            if not compatible_rooms:
                continue  # Lewati jika tidak ada ruangan yang cocok
            
            # Cek dosen jabatan? -> gaboleh senen
            has_jabatan = any(
                dosen_cache[d].jabatan is not None
                for d in class_info["dosen_ids"]
                if d in dosen_cache
            )
            
            assigned = False
            random.shuffle(compatible_rooms)  # Acak urutan ruangan untuk variasi solusi
            
            # Cari semua kemungkinan indeks awal untuk slot waktu berurutan sesuai jumlah SKS
            possible_start_idxs = list(range(len(timeslots_list) - sks + 1))
            random.shuffle(possible_start_idxs)  # Acak urutan indeks untuk variasi solusi
            
          
            preferred_timeslots = []
            non_preferred_timeslots = []
            for idx in possible_start_idxs:
                slots = timeslots_list[idx : idx + sks]
                
                # jika dosen memiliki jabatan, hindari jadwal hari Senin (day_index==0)
                if has_jabatan and slots[0].day_index == 0:
                    continue
                
                slot_ids = {s.id for s in slots}
                # cek apakah semua dosen menyukai slot waktu ini
                is_preferred = all(
                    any(t in preferences_cache.get((oc.id, d), {}).get("preferences", {}) for t in slot_ids)
                    for d in class_info["dosen_ids"]
                )
                
                # Kelompokkan slot waktu berdasarkan preferensi
                if is_preferred:
                    preferred_timeslots.append(idx)
                else:
                    non_preferred_timeslots.append(idx)
            
         
            sorted_start_idxs = preferred_timeslots + non_preferred_timeslots
            
            # coba jadwalkan kelas ke ruangan dan slot waktu yang tersedia
            for room in compatible_rooms:
                if assigned:
                    break
                for start_idx in sorted_start_idxs:
                    slots = timeslots_list[idx : idx + sks]

                    # Pastikan semua slot :
                    #  di hari yang sama
                    #  ga kepotong istirahat
                    # berurutan
                    if not all(
                        slots[i].day_index == slots[0].day_index and 
                        slots[i].id == slots[i-1].id + 1 and
                        slots[i].id not in recess_times
                        for i in range(1, sks)
                    ):
                        continue

                    # Cek ketersediaan slot waktu dan dosen
                    slot_available = True
                    for slot in slots:
                        if (room.id, slot.id) in room_schedule or any(
                            (dosen_id, slot.id) in lecturer_schedule for dosen_id in class_info["dosen_ids"]
                        ):
                            slot_available = False
                            break

                    # Jika semua slot tersedia, jadwalkan kelas
                    if slot_available:
                        for slot in slots:
                            room_schedule[(room.id, slot.id)] = oc.id
                            for dosen_id in class_info["dosen_ids"]:
                                lecturer_schedule[(dosen_id, slot.id)] = oc.id
                        solution.append((oc.id, room.id, slots[0].id))
                        assigned = True
                        break

            # kalo ga ketemu, make fallback
            if not assigned:
                
                best_conflict = float('inf')
                best_assignment = None
                best_slots = None
                best_room = None
                
                # Cari jadwal dengan konflik paling sedikit
                for room in compatible_rooms:
                    for start_idx in possible_start_idxs:
                        slots = timeslots_list[idx : idx + sks]
                        
                        # Pastikan semua slot waktu pada hari yang sama, berurutan, dan tidak bentrok dengan waktu istirahat
                        if not all(
                            slots[i].day_index == slots[0].day_index and 
                            slots[i].id == slots[i-1].id + 1 and
                            slots[i].id not in recess_times
                            for i in range(1, sks)
                        ):
                            continue
                        
                        # Hitung jumlah konflik yang terjadi
                        conflict_cost = sum(
                            (room.id, slot.id) in room_schedule or any(
                                (dosen_id, slot.id) in lecturer_schedule for dosen_id in class_info["dosen_ids"]
                            ) for slot in slots
                        )
                        
                        # Update jadwal terbaik jika ditemukan konflik yang lebih sedikit
                        if conflict_cost < best_conflict:
                            best_conflict = conflict_cost
                            best_assignment = (oc.id, room.id, slots[0].id)
                            best_slots = slots
                            best_room = room
                
                # Terapkan jadwal dengan konflik minimal jika ditemukan
                if best_assignment:
                    for slot in best_slots:
                        room_schedule[(best_room.id, slot.id)] = oc.id
                        for dosen_id in class_info["dosen_ids"]:
                            lecturer_schedule[(dosen_id, slot.id)] = oc.id
                    solution.append(best_assignment)
                    assigned = True
                    
                
        # Tambahkan solusi ke dalam populasi
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


# def generate_fitness_evolution_plot(ga_history, ga_avg_history, sa_history):
#     # Combine GA and SA best fitness history (avoiding duplication at the transition)
#     full_best_fitness = ga_history + sa_history[1:]  # assuming sa_history[0] equals last GA value
#     full_iterations = list(range(1, len(full_best_fitness) + 1))
    
#     fig, ax = plt.subplots(figsize=(15, 8))
#     ax.plot(full_iterations, full_best_fitness, 'b-', linewidth=2, marker='o', markersize=4, label='Best Fitness')
#     ax.axvline(x=len(ga_history), color='red', linestyle='--', linewidth=2, label='GA -> SA Transition')
#     ax.set_title('Evolution of Best Fitness in Hybrid GA-SA', fontsize=16, fontweight='bold')
#     ax.set_xlabel('Iteration')
#     ax.set_ylabel('Best Fitness (Raw)')
#     ax.legend(loc='upper right', fontsize=12)
#     ax.grid(True, linestyle='--', alpha=0.7)
    
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
#     buf.seek(0)
#     plt.close(fig)
#     return base64.b64encode(buf.read()).decode('utf-8')

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
    start_time = datetime.now()
    
    clear_timetable(db)
    logger.info("Hybrid GA-SA scheduling dimulai...")
    courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
    preferences_cache = fetch_dosen_preferences(db, opened_classes)
    dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}
    recess_times = identify_recess_times(timeslot_cache)

    # ------------------------- GA Phase -------------------------
    population = initialize_population(
        opened_classes, rooms, timeslots, population_size,
        opened_class_cache, recess_times, preferences_cache, dosen_cache
    )
    
  
    best_solution_overall = None
    best_fitness_overall = float('inf')
    
    # loop tiap generasi
    for gen in range(generations):
        # seleksi disini make roulette
        selected_pop = roulette_wheel_selection(
            population, opened_class_cache, room_cache, timeslot_cache,
            preferences_cache, dosen_cache, penalties
        )
        new_population = []
        # crossover disini. jadi pasangan yang dipilih dari seleksi akan di crossover disini
        for i in range(0, len(selected_pop), 2):
            if i + 1 < len(selected_pop):
                child1, child2 = crossover(selected_pop[i], selected_pop[i+1])
                new_population.extend([child1, child2])
            else:
                new_population.append(selected_pop[i])
                
            # mutasi disni. acak 1 gen aja dari hasil crossover make probabilitas
        mutated_population = []
        
        # 1 indiv tuh satu jadwal, bukan 1 entri 
        for indiv in new_population:
            mutated_indiv = mutate(
                indiv, opened_classes, rooms, timeslots,
                opened_class_cache, recess_times, preferences_cache, mutation_prob
            )
            mutated_population.append(mutated_indiv)
        population = mutated_population

        best_solution_gen = min(
            population,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        )
        best_fitness_gen = fitness(
            best_solution_gen, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties
        )
        logger.info(f"GA Generation {gen+1}: Best fitness = {best_fitness_gen}")

        # ganti paling baru kalo ketemu yang bagusan
        if best_fitness_gen < best_fitness_overall:
            best_solution_overall = best_solution_gen
            best_fitness_overall = best_fitness_gen

        if best_fitness_gen == 0:
            logger.info("Optimal GA solution found; stopping GA early.")
            population = [best_solution_gen]
            break

    # kalo ga ketemu yang bener2 paling bagus. ambil aja yang paling  kecil
    if best_solution_overall is None:
        best_solution_overall = min(
            population,
            key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
        )
        best_fitness_overall = fitness(
            best_solution_overall, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties
        )
    logger.info(f"GA fase berhasil dengan fitness = {best_fitness_overall}")

    
    best_solution_ga = best_solution_overall
    
    # ------------------------- SA Phase -------------------------
    current_solution = best_solution_ga
    current_fitness = fitness(current_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
    temperature = initial_temperature
    best_solution_sa = current_solution
    best_fitness_sa = current_fitness

    iteration = 0
    # Lanjutkan selama temperatur > 1
    while temperature > 1:
        iteration += 1
        for i in range(iterations_per_temp):
            # Generate neighbor solution
            new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times)
            new_fitness = fitness(new_solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties)
            
            # Update best solution jika lebih bagus
            if new_fitness < best_fitness_sa:
                best_solution_sa = new_solution.copy()
                best_fitness_sa = new_fitness
                logger.info(f"Iterasi SA {iteration}.{i}: Best fitness terbaru = {new_fitness}")
                
                if best_fitness_sa == 0:
                    temperature = 0
                    break
            
            delta_fitness = new_fitness - current_fitness
            acceptance_probability = math.exp(-delta_fitness / temperature) if delta_fitness > 0 else 1.0
            
            if delta_fitness <= 0 or random.random() < acceptance_probability:
                current_solution = new_solution.copy()
                current_fitness = new_fitness
                
        if best_fitness_sa == 0:
            break
            
        temperature *= cooling_rate
        logger.info(f"SA Cooling: Temperature now = {temperature:.2f}")

    # ------------------------- Finalize -------------------------
    formatted_solution = format_solution_for_db(db, best_solution_sa, opened_class_cache, room_cache, timeslot_cache)
    insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)
    
    total_time = datetime.now() - start_time
    logger.info(f"Hybrid GA-SA scheduling completed with final best fitness = {best_fitness_sa}. Total computation time: {total_time}")
        
    constraint_breakdown = {
        "total_fitness": best_fitness_sa
    }
    
    return {
        # "timetable": formatted_solution,
        "computation_time": str(total_time),
        "fitness_details": constraint_breakdown
    }



# =============================================================================
#                        HYBRID GA-SA ENDPOINT
# =============================================================================

@router.post("/generate-schedule-hybrid")
async def generate_schedule_hybrid(
    db: Session = Depends(get_db),
    population_size: int = 50,
    generations: int = 50,
    mutation_prob: float = 0.10,
    initial_temperature: float = 1000,
    cooling_rate: float = 0.95,
    iterations_per_temp: int = 100,
    # PENALTI
    room_conflict: int = Query(2, description="penalti Ruangan bentrok"),
    lecturer_conflict: int = Query(2, description="penalti dosen bentrok"),
    cross_day: int = Query(1, description="Penalti untuk penjadwalan lintas hari"),
    invalid_timeslot: int = Query(2, description="Penalti untuk slot waktu yang tidak valid"),
    wrong_room: int = Query(2, description="Penalti untuk penugasan ruangan yang salah"),
    special_needs: int = Query(2, description="Penalti untuk ketidakpatuhan terhadap kebutuhan khusus"),
    daily_load: int = Query(1, description="Multiplier untuk ketidakseimbangan beban harian"),
    high_priority_preference: int = Query(2, description="Penalti untuk kehilangan preferensi prioritas tinggi"),
    general_preference: int = Query(1, description="Penalti untuk kehilangan preferensi umum"),
    jabatan: int = Query(2, description="Penalti untuk pelanggaran batasan jabatan"),
    conflict_multiplier: int = Query(100, description="Multiplier untuk penalti konflik")
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
            "message": "Schedule berhasil digenerate menggunakan Hybrid GA-SA",
            "computation_time": best_timetable["computation_time"],
            "final_fitness": best_timetable["fitness_details"]
        }
    except Exception as e:
        logger.error(f"Error Hybrid GA-SA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# # import matplotlib.pyplot as plt
# import numpy as np
# import random
# import logging
# from datetime import datetime
# from typing import Any, Dict, List, Optional

# def hybrid_schedule_with_tracking(
#     penalties,
#     db: Session,
#     population_size: int = 50,
#     generations: int = 50,
#     mutation_prob: float = 0.1,
#     initial_temperature: float = 1000,
#     cooling_rate: float = 0.95,
#     iterations_per_temp: int = 100,
# ):
#     start_time = datetime.now()
    
#     clear_timetable(db)
#     logger.info("Starting Hybrid GA-SA scheduling with tracking...")
#     courses, lecturers, rooms, timeslots, preferences, opened_classes, opened_class_cache, room_cache, timeslot_cache = fetch_data(db)
#     preferences_cache = fetch_dosen_preferences(db, opened_classes)
#     dosen_cache = {dosen.pegawai_id: dosen for dosen in lecturers}
#     recess_times = identify_recess_times(timeslot_cache)

#     # Tracking lists for GA and SA best (raw) fitness evolution
#     ga_fitness_history = []
#     sa_fitness_history = []
    
#     # ------------------------- GA Phase -------------------------
#     population = initialize_population(
#         opened_classes, rooms, timeslots, population_size,
#         opened_class_cache, recess_times, preferences_cache
#     )
    
#     best_solution_overall = None
#     best_fitness_overall = float('inf')
    
#     for gen in range(generations):
#         selected_pop = roulette_wheel_selection(
#             population, opened_class_cache, room_cache, timeslot_cache,
#             preferences_cache, dosen_cache, penalties
#         )
#         new_population = []
#         for i in range(0, len(selected_pop), 2):
#             if i + 1 < len(selected_pop):
#                 child1, child2 = crossover(selected_pop[i], selected_pop[i+1])
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.append(selected_pop[i])
#         mutated_population = []
#         for indiv in new_population:
#             mutated_indiv = mutate(
#                 indiv, opened_classes, rooms, timeslots,
#                 opened_class_cache, recess_times, preferences_cache, mutation_prob
#             )
#             mutated_population.append(mutated_indiv)
#         population = mutated_population

#         # Find best solution in current GA generation
#         best_solution_gen = min(
#             population,
#             key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache,
#                                     preferences_cache, dosen_cache, penalties)
#         )
#         best_fitness_gen = fitness(
#             best_solution_gen, opened_class_cache, room_cache, timeslot_cache,
#             preferences_cache, dosen_cache, penalties
#         )
#         logger.info(f"GA Generation {gen+1}: Best fitness (this generation) = {best_fitness_gen}")

#         # Update overall best if current generation is better
#         if best_fitness_gen < best_fitness_overall:
#             best_solution_overall = best_solution_gen
#             best_fitness_overall = best_fitness_gen

#         # Append the overall best raw fitness so far to the GA tracking history
#         ga_fitness_history.append(
#             raw_fitness(best_solution_overall, opened_class_cache, room_cache, timeslot_cache,
#                         preferences_cache, dosen_cache, penalties)
#         )
#         if best_fitness_gen == 0:
#             logger.info("dimal GA solution found; stopping GA early.")
#             population = [best_solution_gen]
#             break

#     if best_solution_overall is None:
#         best_solution_overall = min(
#             population,
#             key=lambda sol: fitness(sol, opened_class_cache, room_cache, timeslot_cache,
#                                     preferences_cache, dosen_cache, penalties)
#         )
#         best_fitness_overall = fitness(
#             best_solution_overall, opened_class_cache, room_cache, timeslot_cache,
#             preferences_cache, dosen_cache, penalties
#         )
#     logger.info(f"GA phase completed with best fitness = {best_fitness_overall}")

#     best_solution_ga = best_solution_overall
    
#     # ------------------------- SA Phase -------------------------
#     current_solution = best_solution_ga
#     current_fitness = best_fitness_overall
#     temperature = initial_temperature
#     best_solution_sa = current_solution
#     best_fitness_sa = current_fitness

#     # Record initial SA raw fitness
#     sa_fitness_history.append(
#         raw_fitness(best_solution_sa, opened_class_cache, room_cache, timeslot_cache,
#                     preferences_cache, dosen_cache, penalties)
#     )
#     iteration = 0
#     while temperature > 1:
#         iteration += 1
#         for i in range(iterations_per_temp):
#             new_solution = generate_neighbor_solution(current_solution, opened_classes, rooms, timeslots, opened_class_cache, recess_times)
#             new_fitness = fitness(new_solution, opened_class_cache, room_cache, timeslot_cache,
#                                   preferences_cache, dosen_cache, penalties)
#             if new_fitness < current_fitness:
#                 current_solution = new_solution
#                 current_fitness = new_fitness
#                 if current_fitness < best_fitness_sa:
#                     best_solution_sa = current_solution
#                     best_fitness_sa = current_fitness
#                     logger.info(f"SA Iteration {iteration}.{i}: New best fitness = {new_fitness}")
#                     if best_fitness_sa == 0:
#                         temperature = 0
#                         break
#         # Record best raw SA fitness at end of this temperature level
#         sa_fitness_history.append(
#             raw_fitness(best_solution_sa, opened_class_cache, room_cache, timeslot_cache,
#                         preferences_cache, dosen_cache, penalties)
#         )
#         if best_fitness_sa == 0:
#             break
#         temperature *= cooling_rate
#         logger.info(f"SA Cooling: Temperature now = {temperature:.2f}")

#     formatted_solution = format_solution_for_db(db, best_solution_sa, opened_class_cache, room_cache, timeslot_cache)
#     insert_timetable(db, formatted_solution, opened_class_cache, room_cache, timeslot_cache)
    
#     total_time = datetime.now() - start_time
#     logger.info(f"Hybrid GA-SA scheduling completed with final best fitness = {best_fitness_sa}. Total computation time: {total_time}")
    
#     raw_conflict = check_conflicts(best_solution_sa, opened_class_cache, room_cache, timeslot_cache, penalties)
#     if raw_conflict > 0:
#         normalized_fitness = best_fitness_sa / penalties["conflict_multiplier"]
#     else:
#         normalized_fitness = best_fitness_sa
#     logger.info(f"Normalized fitness (raw conflict score): {normalized_fitness}")

#     # --- Generate Fitness Evolution Plot ---
#     fitness_plot_base64 = generate_fitness_evolution_plot(ga_fitness_history, None, sa_fitness_history)
    
#     return {
#         "timetable": formatted_solution,
#         "computation_time": str(total_time),
#         "final_fitness": normalized_fitness,
#         "ga_fitness_history": ga_fitness_history,
#         "sa_fitness_history": sa_fitness_history,
#         "fitness_evolution_plot": fitness_plot_base64  
#     }

# # ------------------------- Endpoints -------------------------

# @router.post("/generate-schedule-hybrid-with-tracking")
# async def generate_schedule_hybrid_tracking(
#     db: Session = Depends(get_db),
#     population_size: int = 50,
#     generations: int = 50,
#     mutation_prob: float = 0.10,
#     initial_temperature: float = 1000,
#     cooling_rate: float = 0.95,
#     iterations_per_temp: int = 100,
#     # PENALTY parameters
#     room_conflict: int = Query(70, description="penalti Ruangan bentrok"),
#     lecturer_conflict: int = Query(50, description="penalti dosen bentrok"),
#     cross_day: int = Query(50, description="Penalti untuk penjadwalan lintas hari"),
#     invalid_timeslot: int = Query(50, description="Penalti untuk slot waktu yang tidak valid"),
#     wrong_room: int = Query(30, description="Penalti untuk penugasan ruangan yang salah"),
#     special_needs: int = Query(50, description="Penalti untuk ketidakpatuhan terhadap kebutuhan khusus"),
#     daily_load: int = Query(50, description="Multiplier untuk ketidakseimbangan beban harian"),
#     high_priority_preference: int = Query(50, description="Penalti untuk kehilangan preferensi prioritas tinggi"),
#     general_preference: int = Query(10, description="Penalti untuk kehilangan preferensi umum"),
#     jabatan: int = Query(50, description="Penalti untuk pelanggaran batasan jabatan"),
#     conflict_multiplier: int = Query(100, description="Multiplier untuk penalti konflik")
# ):
#     try:
#         penalties = {
#             "room_conflict": room_conflict,
#             "lecturer_conflict": lecturer_conflict,
#             "cross_day": cross_day,
#             "invalid_timeslot": invalid_timeslot,
#             "wrong_room": wrong_room,
#             "special_needs": special_needs,
#             "daily_load": daily_load,
#             "high_priority_preference": high_priority_preference,
#             "general_preference": general_preference,
#             "jabatan": jabatan,
#             "conflict_multiplier": conflict_multiplier
#         }

#         best_timetable = hybrid_schedule_with_tracking(
#             penalties=penalties,
#             db=db,
#             population_size=population_size,
#             generations=generations,
#             mutation_prob=mutation_prob,
#             initial_temperature=initial_temperature,
#             cooling_rate=cooling_rate,
#             iterations_per_temp=iterations_per_temp
#         )
       
#         return {
#             "message": "Schedule generated successfully using Hybrid GA-SA with tracking",
#             "computation_time": best_timetable["computation_time"],
#             "final_fitness": best_timetable["final_fitness"],
#             "fitness_evolution_plot": best_timetable["fitness_evolution_plot"],
#             "ga_fitness_history": best_timetable["ga_fitness_history"],
#             "sa_fitness_history": best_timetable["sa_fitness_history"]
#         }
#     except Exception as e:
#         logger.error(f"Error generating schedule with Hybrid GA-SA tracking: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

def raw_fitness(solution, opened_class_cache, room_cache, timeslot_cache, preferences_cache, dosen_cache, penalties):
    conflict_score = check_conflicts(solution, opened_class_cache, room_cache, timeslot_cache, penalties)
    if conflict_score > 0:
      
        return conflict_score
    else:
        room_type_score = check_room_type_compatibility(solution, opened_class_cache, room_cache, penalties)
        special_needs_score = check_special_needs_compliance(solution, opened_class_cache, room_cache, preferences_cache, penalties)
        daily_load_score = check_daily_load_balance(solution, opened_class_cache, timeslot_cache, penalties)
        preference_score = check_preference_compliance(solution, opened_class_cache, timeslot_cache, preferences_cache, penalties)
        jabatan_penalty = check_jabatan_constraint(solution, opened_class_cache, timeslot_cache, dosen_cache, penalties)
        return room_type_score + special_needs_score + daily_load_score + preference_score + jabatan_penalty
