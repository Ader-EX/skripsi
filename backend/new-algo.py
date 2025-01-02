import pandas as pd
import random
from datetime import datetime, timedelta
import time

# Reload the required data files
mata_kuliah_file_path = './datas/MataKuliah.csv'
dosen_file_path = './datas/Dosen.csv'
ruangan_file_path = './datas/CleanedRuangan.csv'
lecturer_preference_file_path = './datas/lecturer_time_preferences.csv'

pengajaran_file_path = "./datas/fixed_pengajaran.csv"

mata_kuliah_df = pd.read_csv(mata_kuliah_file_path)
dosen_df = pd.read_csv(dosen_file_path)
ruangan_df = pd.read_csv(ruangan_file_path)
lecturer_time_preferences_df = pd.read_csv(lecturer_preference_file_path)
pengajaran_df = pd.read_csv(pengajaran_file_path)

print("Columns in pengajaran_df:", pengajaran_df.columns)

# Create a mapping of mk_id to allowed dosens
pengajaran_mapping = pengajaran_df.groupby("mk_id")["dosen_id"].apply(list).to_dict()

# Create a separate mapping for dosen_besar (is_dosen_kb = True)
dosen_besar_mapping = pengajaran_df[pengajaran_df["is_dosen_kb"] == True].set_index("mk_id")["dosen_id"].to_dict()

# Ensure `f_pegawai_id` is treated as a string
dosen_df['f_pegawai_id'] = dosen_df['f_pegawai_id'].astype(str).str.strip()
dosen_df['jabatan'] = dosen_df['jabatan'].fillna("")  # Replace NaN with an empty string

room_data = ruangan_df.set_index('f_koderuang').to_dict(orient='index')
dosen_data = dosen_df.set_index('f_pegawai_id').to_dict(orient='index')


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


# Validate lecturer assignment based on pengajaran.csv
def is_valid_assignment(dosen_id, mk_id):
    # Validate dosen_id and mk_id against pengajaran.csv
    valid_entries = pengajaran_df[
        (pengajaran_df['dosen_id'] == dosen_id) &
        (pengajaran_df['mk_id'] == mk_id)
        ]
    return not valid_entries.empty

def generate_combined_schedule(pengajaran_df, adjusted_time_slots):
    schedule = []
    no = 1
    class_time_slots = {}
    class_rooms = {}
    time_slot_usage = {}
    room_time_usage = {}

    grouped_pengajaran = pengajaran_df.groupby("mk_id")
    for mk_id, group in grouped_pengajaran:
        matakuliah_name = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "Namamk"].values[0]
        kurikulum = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "kurikulum"].values[0]
        sks = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "sks"].values[0]
        semester = mata_kuliah_df.loc[mata_kuliah_df["Kodemk"] == mk_id, "smt"].values[0]

        # Assign a uniform time slot for this lecture
        base_time_slot = assign_time_slot(adjusted_time_slots, time_slot_usage)
        time_key = (base_time_slot["day"], base_time_slot["start_time"], base_time_slot["end_time"])

        # Assign rooms for each class
        available_rooms = list(room_data.keys())
        for class_label in group["class"].unique():
            room = assign_room(room_time_usage, base_time_slot, available_rooms)
            class_rooms[class_label] = room

            # Add entries for Kelas Kecil
            for _, row in group[group["class"] == class_label].iterrows():
                jadwal_pertemuan = (
                    f"{base_time_slot['day']} - "
                    f"{base_time_slot['start_time'].strftime('%H:%M')}-"
                    f"{base_time_slot['end_time'].strftime('%H:%M')} "
                    f"( {room} )"
                )
                schedule.append({
                    "No": no,
                    "Kodemk": mk_id,
                    "Matakuliah": matakuliah_name,
                    "Kurikulum": kurikulum,
                    "Kelas": f"Kelas Kecil {class_label}",
                    "Kap/Peserta": "35 / 35",
                    "Sks": sks,
                    "Smt": semester,
                    "Jadwal Pertemuan": jadwal_pertemuan,
                    "Dosen": f"{dosen_data[str(row['dosen_id'])]['f_namapegawai']}",
                    "Dosen ID": row["dosen_id"],
                })
                no += 1

        # Add entry for Kelas Besar if applicable
        dosen_kb_row = group[group["is_dosen_kb"] == True]
        if not dosen_kb_row.empty:
            dosen_kb_id = dosen_kb_row["dosen_id"].iloc[0]
            dosen_kb_name = dosen_data[str(dosen_kb_id)]["f_namapegawai"]
            jadwal_pertemuan_kb = (
                f"{base_time_slot['day']} - "
                f"{base_time_slot['start_time'].strftime('%H:%M')}-"
                f"{base_time_slot['end_time'].strftime('%H:%M')} "
                f"( VCR-FIK-KB-1 )"
            )
            schedule.append({
                "No": no,
                "Kodemk": mk_id,
                "Matakuliah": matakuliah_name,
                "Kurikulum": kurikulum,
                "Kelas": "Kelas Besar",
                "Kap/Peserta": "100 / 100",
                "Sks": sks,
                "Smt": semester,
                "Jadwal Pertemuan": jadwal_pertemuan_kb,
                "Dosen": f"{dosen_kb_name}",
                "Dosen ID": dosen_kb_id,
            })
            no += 1

    return schedule








def assign_special_room(room_time_usage, time_slot, available_rooms):
    """Assign a room based on specific criteria (Praktikum or Non-Praktikum)."""
    time_key = (time_slot["day"], time_slot["start_time"], time_slot["end_time"])
    for room in available_rooms.keys():
        if time_key not in room_time_usage.get(room, set()):
            room_time_usage.setdefault(room, set()).add(time_key)
            return room
    fallback_room = list(available_rooms.keys())[0]
    room_time_usage.setdefault(fallback_room, set()).add(time_key)
    return fallback_room


def calculate_fitness(schedule):
    penalties = 0
    dosen_time_usage = {}
    room_time_usage = {}

    for entry in schedule:
        f_pegawai_id = entry["Dosen ID"]
        jadwal = entry["Jadwal Pertemuan"]
        room = jadwal.split("(")[-1][:-1].strip()

        # Parse time slot
        try:
            jadwal_parts = jadwal.split(" - ")
            day = jadwal_parts[0]
            start_time, end_time = jadwal_parts[1].split(" - ")
        except IndexError:
            continue  # Skip malformed entries

        time_key = (day, start_time, end_time)

        # Duplicate time slot penalty
        if f_pegawai_id in dosen_time_usage and time_key in dosen_time_usage[f_pegawai_id]:
            penalties += 20
        dosen_time_usage.setdefault(f_pegawai_id, set()).add(time_key)

        # Room conflict penalty
        if room in room_time_usage and time_key in room_time_usage[room]:
            penalties += 20
        room_time_usage.setdefault(room, set()).add(time_key)

    return -penalties

def assign_time_slot(adjusted_time_slots, time_slot_usage):
    for time_slot in adjusted_time_slots:
        time_key = (time_slot["day"], time_slot["start_time"], time_slot["end_time"])
        if time_key not in time_slot_usage:
            time_slot_usage[time_key] = True
            return time_slot
    # Fallback to random
    return random.choice(adjusted_time_slots)

def assign_room(room_time_usage, time_slot, available_rooms):
    time_key = (time_slot["day"], time_slot["start_time"], time_slot["end_time"])
    for room in available_rooms:
        if time_key not in room_time_usage.get(room, set()):
            room_time_usage.setdefault(room, set()).add(time_key)
            return room
    return random.choice(available_rooms)

def parse_jadwal(jadwal):
    try:
        jadwal_parts = jadwal.split("(")
        time_and_day = jadwal_parts[0].strip()
        room = jadwal_parts[1][:-1].strip()  # Extract room, e.g., "FIKLAB-401"

        day, time_range = time_and_day.split(" - ", 1)
        start_time, end_time = time_range.split("-")
        return day.strip(), start_time.strip(), end_time.strip(), room.strip()
    except (IndexError, ValueError) as e:
        print(f"Malformed Jadwal Pertemuan: {jadwal}")
        return None, None, None, None


def calculate_fitness(schedule):
    penalties = 0
    dosen_time_usage = {}
    room_time_usage = {}

    # Convert lecturer preferences to a dictionary for faster lookups
    lecturer_preferences = {}
    for _, row in lecturer_time_preferences_df.iterrows():
        f_pegawai_id = str(row["f_pegawai_id"]).strip()
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
        f_pegawai_id = str(entry.get("Dosen ID", "")).strip()
        jadwal = entry.get("Jadwal Pertemuan", "")

        # Parse Jadwal Pertemuan
        day, start_time, end_time, room = parse_jadwal(jadwal)

        # Skip if parsing fails
        if not day or not start_time or not end_time or not room:
            print(f"Malformed Jadwal Pertemuan: {jadwal}")
            penalties += 50  # Penalize malformed entries heavily
            continue

        time_key = (day, start_time, end_time)

        # Skip entry without a valid lecturer ID or subject
        if not f_pegawai_id or not entry.get("Matakuliah"):
            continue

        # HARD CONSTRAINT: DUPLICATE TEACHING TIME
        if (f_pegawai_id, time_key) in seen_slots:
            penalties += 20
        seen_slots.add((f_pegawai_id, time_key))

        # Penalize if a lecturer or room is scheduled in overlapping slots
        if time_key in dosen_time_usage.get(f_pegawai_id, set()):
            penalties += 20
        if time_key in room_time_usage.get(room, set()):
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
                (pref for pref in preferences if
                 pref["day"] == day and pref["start_time"] == start_time and pref["end_time"] == end_time),
                None
            )

            if not preferred_slot:
                penalties += 20  # Penalize if not in preferences
            elif not preferred_slot["high_preference"]:
                penalties += 20  # Penalize non-high-preference slots

        # Track room and dosen usage
        dosen_time_usage.setdefault(f_pegawai_id, set()).add(time_key)
        room_time_usage.setdefault(room, set()).add(time_key)

    return -penalties




def genetic_algorithm(population_size, generations, mutation_rate):
    population = [generate_combined_schedule(pengajaran_df, adjusted_time_slots)
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
            new_time = random.choice(adjusted_time_slots)

            # Assign new room based on class type
            if "Kelas Kecil" in entry["Kelas"]:
                class_label = entry["Kelas"].split(" ")[-1]
                room_num = 300 + (ord(class_label) - ord('A'))
                new_room = f"FIK-{room_num}"
            else:  # For Kelas Besar
                new_room = "VCR-FIK-KB-1"

            # Update Jadwal Pertemuan
            entry["Jadwal Pertemuan"] = (
                f"{new_time['day']} - "
                f"{new_time['start_time'].strftime('%H:%M')} - "
                f"{new_time['end_time'].strftime('%H:%M')} "
                f"( {new_room} )"
            )

    return schedule



# Run the genetic algorithm
population_size = 100  # Size of the population
generations = 50  # Number of generations
mutation_rate = 0.1  # Mutation rate


def calculate_fitness_percentage(best_fitness, total_entries, penalties_per_entry):
    worst_case_penalty = total_entries * penalties_per_entry
    fitness_percentage = (1 - abs(best_fitness) / worst_case_penalty) * 100
    return fitness_percentage

def merge_schedule(schedule):
    """
    Merge rows with the same Kelas, aggregating Dosen and Dosen ID.
    """
    import pandas as pd

    # Convert the schedule to a DataFrame
    df = pd.DataFrame(schedule)

    # Ensure 'Dosen ID' is treated as a string
    df['Dosen ID'] = df['Dosen ID'].astype(str)

    # Group by relevant columns and aggregate Dosen and Dosen ID
    merged_df = df.groupby(
        ["Kodemk", "Matakuliah", "Kurikulum", "Kelas", "Kap/Peserta", "Sks", "Smt", "Jadwal Pertemuan"],
        as_index=False
    ).agg({
        "Dosen": lambda x: "; ".join(x),
        "Dosen ID": lambda x: "; ".join(x)
    })

    # Renumber the "No" column
    merged_df.insert(0, "No", range(1, len(merged_df) + 1))

    # Convert back to a list of dictionaries if needed
    merged_schedule = merged_df.to_dict(orient='records')
    return merged_schedule




total_entries = len(pengajaran_df)
penalties_per_entry = 60

# Run the genetic algorithm
start_time = time.time()
best_schedule, best_fitness = genetic_algorithm(population_size, generations, mutation_rate)
merged_schedule = merge_schedule(best_schedule)
end_time = time.time()

# Calculate percentage fitness
fitness_percentage = calculate_fitness_percentage(best_fitness, total_entries, penalties_per_entry)

# Save the best schedule to a CSV file
best_schedule_df = pd.DataFrame(merged_schedule)
best_schedule_df.to_csv("./datas/hasil/BestSchedule.csv", index=False)

# Display results
print(f"Genetic Algorithm completed in {end_time - start_time:.2f} seconds")
print(f"Best Fitness Score: {best_fitness}")
print(f"Fitness Percentage: {fitness_percentage:.2f}%")
print("Best schedule saved to './datas/hasil/BestSchedule.csv'")
