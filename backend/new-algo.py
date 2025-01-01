import pandas as pd
import random
from datetime import datetime, timedelta
import time

# Reload the required data files
mata_kuliah_file_path = './datas/MataKuliah.csv'
dosen_file_path = './datas/Dosen.csv'
ruangan_file_path = './datas/CleanedRuangan.csv'
lecturer_preference_file_path = './datas/lecturer_time_preferences.csv'

pengajaran_file_path = "./datas/pengajaran.csv"

pengajaran_file_path = "./datas/pengajaran.csv"
pengajaran_df = pd.read_csv(pengajaran_file_path)


mata_kuliah_df = pd.read_csv(mata_kuliah_file_path)
dosen_df = pd.read_csv(dosen_file_path)
ruangan_df = pd.read_csv(ruangan_file_path)
lecturer_time_preferences_df = pd.read_csv(lecturer_preference_file_path)
pengajaran_df = pd.read_csv(pengajaran_file_path)

print("[DEBUG] pengajaran_df with is_dosen_kb == True:")
print(pengajaran_df[pengajaran_df["is_dosen_kb"] == True])


# Create a mapping of mk_id to allowed dosens
pengajaran_mapping = pengajaran_df.groupby("mk_id")["dosen_id"].apply(list).to_dict()

# Create a separate mapping for dosen_besar (is_dosen_kb = True)
dosen_besar_mapping = pengajaran_df[pengajaran_df["is_dosen_kb"] == True].set_index("mk_id")["dosen_id"].to_dict()

# Ensure `f_pegawai_id` is treated as a string
dosen_df['f_pegawai_id'] = dosen_df['f_pegawai_id'].astype(str).str.strip()
dosen_df['jabatan'] = dosen_df['jabatan'].fillna("")  # Replace NaN with an empty string

room_data = ruangan_df.set_index('f_koderuang').to_dict(orient='index')
dosen_data = dosen_df.set_index('f_pegawai_id').to_dict(orient='index')

print(pengajaran_df.columns)



# Generate adjusted time slots
def generate_adjusted_time_slots(start_time, end_time, interval_minutes=50):
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    slots = []
    for day in days:
        current_time = start_time
        while current_time < end_time:
            slot_end_time = current_time + timedelta(minutes=interval_minutes)
            if not (datetime(2024, 1, 1, 12, 0) <= current_time < datetime(2024, 1, 1, 13, 0)):
                slots.append({
                    "day": day,
                    "time_slot_id": len(slots) + 1,
                    "start_time": current_time,
                    "end_time": slot_end_time
                })
            current_time = slot_end_time
    return slots

adjusted_time_slots = generate_adjusted_time_slots(
    start_time=datetime(2024, 1, 1, 7, 0),
    end_time=datetime(2024, 1, 1, 18, 0)
)

# Generate teaching assignments
# Generate teaching assignments based on the "kelas" column
def generate_pengajaran_table():
    valid_f_pegawai_ids = dosen_df['f_pegawai_id'].dropna().unique().tolist()
    pengajaran = []

    for _, row in mata_kuliah_df.iterrows():
        mata_kuliah_id = row["Kodemk"]

        # Interpret the `kelas` column as a string of class labels
        kelas_labels = list(row["kelas"].strip())  # Convert 'ABCDE' to ['A', 'B', 'C', 'D', 'E']

        # Get the list of dosens for this mata kuliah
        dosens_for_mk = pengajaran_df[pengajaran_df["mk_id"] == mata_kuliah_id]

        # Get the dosen besar (is_dosen_kb == True)
        dosen_besar_row = dosens_for_mk[dosens_for_mk["is_dosen_kb"] == True]
        dosen_besar_id = dosen_besar_row["dosen_id"].iloc[0] if not dosen_besar_row.empty else None

        for class_label in kelas_labels:
            if dosen_besar_id:
                # Assign dosen besar to the first class
                pengajaran.append({
                    "mk_id": mata_kuliah_id,
                    "class": class_label,
                    "dosen_id": dosen_besar_id,
                    "is_dosen_kb": True  # Mark as dosen besar
                })
                dosen_besar_id = None  # Ensure only one "dosen besar" is added
            else:
                # Assign other dosens (dosen kecil)
                dosen_kecil_row = dosens_for_mk[dosens_for_mk["is_dosen_kb"] == False]
                if not dosen_kecil_row.empty:
                    f_pegawai_id = dosen_kecil_row["dosen_id"].sample().iloc[0]
                else:
                    f_pegawai_id = random.choice(valid_f_pegawai_ids)

                pengajaran.append({
                    "mk_id": mata_kuliah_id,
                    "class": class_label,
                    "dosen_id": f_pegawai_id,
                    "is_dosen_kb": False  # Mark as dosen kecil
                })

    return pd.DataFrame(pengajaran)




pengajaran_table = generate_pengajaran_table()
print(pengajaran_table.columns)
print(pengajaran_table.head())

# Generate formatted schedule without time preferences

# def generate_formatted_schedule(pengajaran_table, adjusted_time_slots):
#     schedule = []
#     no = 1

#     for _, row in pengajaran_table.iterrows():
#         mk_id = row["mata_kuliah_id"]
#         class_type = row["class"]

#         # Skip if mk_id is not in the pengajaran mapping
#         if mk_id not in pengajaran_mapping:
#             continue

#         # Assign dosen besar
#         dosen_besar = dosen_besar_mapping.get(mk_id)
#         if dosen_besar:
#             room = random.choice(list(room_data.keys()))
#             time_slot = random.choice(adjusted_time_slots)

#             schedule.append({
#                 "No": no,
#                 "Kodemk": mk_id,
#                 "Matakuliah": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "Namamk"].values[0],
#                 "Kurikulum": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "kurikulum"].values[0],
#                 "Kelas": class_type,
#                 "Kap/Peserta": f"0 / {room_data[room]['f_kapasitas_kuliah']}",
#                 "Sks": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "sks"].values[0],
#                 "Smt": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "smt"].values[0],
#                 "Jadwal Pertemuan": f"{time_slot['day']} - {time_slot['start_time'].strftime('%H:%M')} - {time_slot['end_time'].strftime('%H:%M')} ({room})",
#                 "Dosen": dosen_data[dosen_besar]["f_namapegawai"],
#                 "Dosen ID": dosen_besar
#             })
#             no += 1

#         # Assign dosen kecil (if any)
#         dosen_kecil_list = [d for d in pengajaran_mapping[mk_id] if d != dosen_besar]
#         if dosen_kecil_list:
#             for dosen_kecil in dosen_kecil_list:
#                 room = random.choice(list(room_data.keys()))
#                 time_slot = random.choice(adjusted_time_slots)

#                 schedule.append({
#                     "No": no,
#                     "Kodemk": mk_id,
#                     "Matakuliah": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "Namamk"].values[0],
#                     "Kurikulum": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "kurikulum"].values[0],
#                     "Kelas": class_type,
#                     "Kap/Peserta": f"0 / {room_data[room]['f_kapasitas_kuliah']}",
#                     "Sks": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "sks"].values[0],
#                     "Smt": mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "smt"].values[0],
#                     "Jadwal Pertemuan": f"{time_slot['day']} - {time_slot['start_time'].strftime('%H:%M')} - {time_slot['end_time'].strftime('%H:%M')} ({room})",
#                     "Dosen": dosen_data[dosen_kecil]["f_namapegawai"],
#                     "Dosen ID": dosen_kecil
#                 })
#                 no += 1

#     return schedule

def generate_formatted_schedule(pengajaran_table, adjusted_time_slots):
    schedule = []
    no = 1

    # Ensure mk_id and is_dosen_kb are properly formatted
    pengajaran_table["mk_id"] = pengajaran_table["mk_id"].astype(str).str.strip()
    pengajaran_table["is_dosen_kb"] = pengajaran_table["is_dosen_kb"].astype(bool)

    # Group by Mata Kuliah (mk_id)
    grouped_pengajaran = pengajaran_table.groupby("mk_id")
    for mk_id, group in grouped_pengajaran:
        print(f"[DEBUG] Processing mk_id: {mk_id}")
        print(group)

        # Mata Kuliah details
        matakuliah_name = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "Namamk"].values[0]
        kurikulum = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "kurikulum"].values[0]
        sks = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "sks"].values[0]
        semester = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "smt"].values[0]

        # Handle Kelas Besar
        dosen_besar_row = group[group["is_dosen_kb"] == True]
        if not dosen_besar_row.empty:
        
            dosen_besar_id = dosen_besar_row["dosen_id"].iloc[0]
            print(f"[DEBUG] Dosen besar found for mk_id {mk_id}: {dosen_besar_id}")
            dosen_besar_name = dosen_data[str(dosen_besar_id)]["f_namapegawai"]

            schedule.append({
                "No": no,
                "Kodemk": mk_id,
                "Matakuliah": matakuliah_name,
                "Kurikulum": kurikulum,
                "Kelas": "Kelas Besar",
                "Kap/Peserta": f"{len(group) * 35} / {len(group) * 35}",
                "Sks": sks,
                "Smt": semester,
                "Jadwal Pertemuan": "Jumat - 08:00-09:40 (VCR-FIK-KB-1)",
                "Dosen": dosen_besar_name,
                "Dosen ID": dosen_besar_id,
            })
            no += 1
        else:
            print(f"[DEBUG] No dosen besar found for mk_id: {mk_id}")

        # Handle Kelas Kecil
        dosen_kecil_rows = group[group["is_dosen_kb"] == False]
        for _, row in dosen_kecil_rows.iterrows():
            dosen_kecil_id = row["dosen_id"]
            dosen_kecil_name = dosen_data[str(dosen_kecil_id)]["f_namapegawai"]

            class_time_slot = random.choice(adjusted_time_slots)
            room = random.choice(list(room_data.keys()))
            schedule.append({
                "No": no,
                "Kodemk": mk_id,
                "Matakuliah": matakuliah_name,
                "Kurikulum": kurikulum,
                "Kelas": f"Kelas Kecil {row['class']}",
                "Kap/Peserta": "35 / 35",
                "Sks": sks,
                "Smt": semester,
                "Jadwal Pertemuan": f"{class_time_slot['day']} - {class_time_slot['start_time'].strftime('%H:%M')} - {class_time_slot['end_time'].strftime('%H:%M')} ({room})",
                "Dosen": dosen_kecil_name,
                "Dosen ID": dosen_kecil_id,
            })
            no += 1

    return schedule




# Fitness calculation
# Fitness calculation with additional constraint for "tugas tambahan"

def calculate_fitness(schedule):
    penalties = 0
    dosen_time_usage = {}
    room_time_usage = {}

    # Convert lecturer preferences to a dictionary for faster lookups
    lecturer_preferences = {}
    for _, row in lecturer_time_preferences_df.iterrows():
        f_pegawai_id = str(row["f_pegawai_id"]).strip()  # Correct variable here
        day = row["day"]
        start_time = row["start_time"]
        end_time = row["end_time"]
        high_preference = row["high_preference"]
        if f_pegawai_id not in lecturer_preferences:
            lecturer_preferences[f_pegawai_id] = []
        lecturer_preferences[f_pegawai_id].append({
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "high_preference": high_preference,
        })

    seen_slots = set()
    for entry in schedule:
        f_pegawai_id = str(entry.get("Dosen ID", "")).strip()  # Ensure this is a string
        jadwal = entry["Jadwal Pertemuan"]

        try:
            # Split Jadwal Pertemuan into components
            jadwal_parts = jadwal.split(" - ")
            day = jadwal_parts[0]  # The day, e.g., "Selasa"
            time_range = jadwal_parts[1:3]  # ["07:50", "08:40"]
            start_time, end_time = time_range
            room = jadwal.split("(")[-1][:-1]  # Extract room, e.g., "FIKLAB-401"

        except (IndexError, ValueError):
            print(f"Malformed Jadwal Pertemuan: {jadwal}")
            continue  # Skip malformed schedule entries

        # Skip entry tanpa kelas matakuliah
        if not f_pegawai_id or not entry.get("Matakuliah"):
            continue

        # HARD CONSTRAINT: DUPLICATE TEACHING TIME
        if (f_pegawai_id, f"{day} {start_time}-{end_time}") in seen_slots:
            penalties += 20
        seen_slots.add((f_pegawai_id, f"{day} {start_time}-{end_time}"))

        # Penalize if a lecturer or room is scheduled in overlapping slots
        if f"{day} {start_time}-{end_time}" in dosen_time_usage.get(f_pegawai_id, set()):
            penalties += 20
        if f"{day} {start_time}-{end_time}" in room_time_usage.get(room, set()):
            penalties += 20

        # Penalize if a lecturer with "tugas tambahan" is scheduled on Monday
        if day == "Senin" and f_pegawai_id in dosen_data:
            jabatan = dosen_data[f_pegawai_id].get("jabatan", "").strip()
            if jabatan:  # Non-empty `jabatan` indicates "tugas tambahan"
                penalties += 20

        # HARD CONSTRAINT: Time Preferences
        if f_pegawai_id in lecturer_preferences:
            preferences = lecturer_preferences[f_pegawai_id]
            preferred_slot = next(
                (pref for pref in preferences if pref["day"] == day and pref["start_time"] == start_time and pref["end_time"] == end_time),
                None
            )

            if not preferred_slot:
                penalties += 20  # Penalize if not in preferences
            elif not preferred_slot["high_preference"]:
                penalties += 20  # Penalize non-high-preference slots

        # Track room and dosen usage
        dosen_time_usage.setdefault(f_pegawai_id, set()).add(f"{day} {start_time}-{end_time}")
        room_time_usage.setdefault(room, set()).add(f"{day} {start_time}-{end_time}")

    return -penalties

# def calculate_fitness(schedule):
#     penalties = 0
#     dosen_time_usage = {}
#     room_time_usage = {}

#     seen_slots = set()
#     for entry in schedule:
#         f_pegawai_id = entry.get("Dosen ID", "").strip()
#         room_id = entry["Jadwal Pertemuan"].split('(')[1][:-1]
#         time_slot = entry["Jadwal Pertemuan"].split(' - ')[1]
#         day = entry["Jadwal Pertemuan"].split(" - ")[0]

#         # Skip room-only entries (no associated lecturer or class)
#         if not f_pegawai_id or not entry.get("Matakuliah"):
#             continue

#         # Penalize duplicate lecturer time slots
#         if (f_pegawai_id, time_slot) in seen_slots:
#             penalties += 20
#         seen_slots.add((f_pegawai_id, time_slot))

#         # Penalize if a lecturer or room is scheduled in overlapping slots
#         if time_slot in dosen_time_usage.get(f_pegawai_id, set()):
#             penalties += 20
#         if time_slot in room_time_usage.get(room_id, set()):
#             penalties += 20

#         # Penalize if a lecturer with "tugas tambahan" is scheduled on Monday
#         if day == "Senin" and f_pegawai_id in dosen_data:
#             jabatan = dosen_data[f_pegawai_id].get("jabatan", "").strip()
#             if jabatan:  # Non-empty `jabatan` indicates "tugas tambahan"
#                 penalties += 20

#         # Track room and dosen usage
#         dosen_time_usage.setdefault(f_pegawai_id, set()).add(time_slot)
#         room_time_usage.setdefault(room_id, set()).add(time_slot)

#     return -penalties



# Genetic algorithm
def genetic_algorithm(population_size, generations, mutation_rate):
    population = [generate_formatted_schedule(pengajaran_table, adjusted_time_slots)
                  for _ in range(population_size)]
    best_schedule = None
    best_fitness = float('-inf')

    for generation in range(1, generations + 1):
        fitness_scores = [calculate_fitness(ind) for ind in population]
        best_generation_fitness = max(fitness_scores)
        avg_generation_fitness = sum(fitness_scores) / len(fitness_scores)

        best_index = fitness_scores.index(best_generation_fitness)
        if best_generation_fitness > best_fitness:
            best_fitness = best_generation_fitness
            best_schedule = population[best_index]

        print(f"Generation {generation}/{generations}")
        print(f"  Best Fitness: {best_generation_fitness}")
        print(f"  Average Fitness: {avg_generation_fitness:.2f}")

        # Create next generation
        next_generation = []
        for _ in range(population_size // 2):
            parent1, parent2 = select_parents(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2)
            next_generation.append(mutate(child1, mutation_rate))
            next_generation.append(mutate(child2, mutation_rate))

        population = next_generation

    return best_schedule, best_fitness

# Parent selection
def select_parents(population, fitness_scores):
    total_fitness = sum(fitness_scores)
    probabilities = [score / total_fitness for score in fitness_scores]
    return random.choices(population, probabilities, k=2)

# Crossover
def crossover(parent1, parent2):
    point = random.randint(1, len(parent1) - 1)
    return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]

# Mutation
def mutate(schedule, mutation_rate=0.1):
    for entry in schedule:
        if random.random() < mutation_rate:
            new_time_slot = random.choice(adjusted_time_slots)
            new_room = random.choice(list(room_data.keys()))
            entry["Jadwal Pertemuan"] = f"{new_time_slot['day']} - {new_time_slot['start_time'].strftime('%H:%M')} - {new_time_slot['end_time'].strftime('%H:%M')} ({new_room})"
    return schedule

# Run the genetic algorithm
population_size = 100  # Size of the population
generations = 50       # Number of generations
mutation_rate = 0.1    # Mutation rate
def calculate_fitness_percentage(best_fitness, total_entries, penalties_per_entry):
    worst_case_penalty = total_entries * penalties_per_entry
    fitness_percentage = (1 - abs(best_fitness) / worst_case_penalty) * 100
    return fitness_percentage

# Define total entries and penalties per entry
total_entries = len(pengajaran_table)  # Number of schedule entries
penalties_per_entry = 60  # Sum of all penalties per entry

# Run the genetic algorithm
start_time = time.time()
best_schedule, best_fitness = genetic_algorithm(population_size, generations, mutation_rate)
end_time = time.time()

# Calculate percentage fitness
fitness_percentage = calculate_fitness_percentage(best_fitness, total_entries, penalties_per_entry)

# Save the best schedule to a CSV file
best_schedule_df = pd.DataFrame(best_schedule)
best_schedule_df.to_csv("./datas/hasil/BestSchedule.csv", index=False)

# Display results
print(f"Genetic Algorithm completed in {end_time - start_time:.2f} seconds")
print(f"Best Fitness Score: {best_fitness}")
print(f"Fitness Percentage: {fitness_percentage:.2f}%")
print("Best schedule saved to './datas/hasil/BestSchedule.csv'")