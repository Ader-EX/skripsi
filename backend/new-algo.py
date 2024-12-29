import pandas as pd
import random
from datetime import datetime, timedelta
import time

# Reload the required data files
mata_kuliah_file_path = './datas/MataKuliah.csv'
dosen_file_path = './datas/Dosen.csv'
ruangan_file_path = './datas/CleanedRuangan.csv'

mata_kuliah_df = pd.read_csv(mata_kuliah_file_path)
dosen_df = pd.read_csv(dosen_file_path)
ruangan_df = pd.read_csv(ruangan_file_path)

# Ensure `f_pegawai_id` is treated as a string
dosen_df['f_pegawai_id'] = dosen_df['f_pegawai_id'].astype(str).str.strip()
dosen_df['jabatan'] = dosen_df['jabatan'].fillna("")  # Replace NaN with an empty string

room_data = ruangan_df.set_index('f_koderuang').to_dict(orient='index')
dosen_data = dosen_df.set_index('f_pegawai_id').to_dict(orient='index')

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
        
        for class_label in kelas_labels:
            f_pegawai_id = random.choice(valid_f_pegawai_ids)  # Randomly assign a lecturer
            pengajaran.append({
                "mata_kuliah_id": mata_kuliah_id,
                "class": class_label,
                "f_pegawai_id": f_pegawai_id,
            })
    
    return pd.DataFrame(pengajaran)


pengajaran_table = generate_pengajaran_table()

# Generate formatted schedule without time preferences
def generate_formatted_schedule(pengajaran_table, adjusted_time_slots):
    schedule = []
    no = 1

    for _, row in pengajaran_table.iterrows():
        mata_kuliah_id = row["mata_kuliah_id"]
        class_type = row["class"]
        f_pegawai_id = str(row["f_pegawai_id"]).strip()

        if f_pegawai_id not in dosen_data:
            continue

        dosen_name = dosen_data[f_pegawai_id]["f_namapegawai"]
        room = random.choice(list(room_data.keys()))
        time_slot = random.choice(adjusted_time_slots)

        matakuliah_name = mata_kuliah_df.loc[mata_kuliah_df['Kodemk'] == mata_kuliah_id, 'Namamk'].values[0]
        kurikulum = mata_kuliah_df.loc[mata_kuliah_df['Kodemk'] == mata_kuliah_id, 'kurikulum'].values[0]
        sks = mata_kuliah_df.loc[mata_kuliah_df['Kodemk'] == mata_kuliah_id, 'sks'].values[0]
        semester = mata_kuliah_df.loc[mata_kuliah_df['Kodemk'] == mata_kuliah_id, 'smt'].values[0]

        room_capacity = room_data[room]["f_kapasitas_kuliah"]
        kap_peserta = f"0 / {room_capacity}"

        schedule.append({
            "No": no,
            "Kodemk": mata_kuliah_id,
            "Matakuliah": matakuliah_name,
            "Kurikulum": kurikulum,
            "Kelas": class_type,
            "Kap/Peserta": kap_peserta,
            "Sks": sks,
            "Smt": semester,
            "Jadwal Pertemuan": f"{time_slot['day']} - {time_slot['start_time'].strftime('%H:%M')} - {time_slot['end_time'].strftime('%H:%M')} ({room})",
            "Dosen": dosen_name,
            "Dosen ID": f_pegawai_id
        })
        no += 1

    return schedule

# Fitness calculation
# Fitness calculation with additional constraint for "tugas tambahan"
def calculate_fitness(schedule):
    penalties = 0
    dosen_time_usage = {}
    room_time_usage = {}

    seen_slots = set()
    for entry in schedule:
        f_pegawai_id = entry.get("Dosen ID", "").strip()
        room_id = entry["Jadwal Pertemuan"].split('(')[1][:-1]
        time_slot = entry["Jadwal Pertemuan"].split(' - ')[1]
        day = entry["Jadwal Pertemuan"].split(" - ")[0]

        # Skip room-only entries (no associated lecturer or class)
        if not f_pegawai_id or not entry.get("Matakuliah"):
            continue

        # Penalize duplicate lecturer time slots
        if (f_pegawai_id, time_slot) in seen_slots:
            penalties += 20
        seen_slots.add((f_pegawai_id, time_slot))

        # Penalize if a lecturer or room is scheduled in overlapping slots
        if time_slot in dosen_time_usage.get(f_pegawai_id, set()):
            penalties += 20
        if time_slot in room_time_usage.get(room_id, set()):
            penalties += 20

        # Penalize if a lecturer with "tugas tambahan" is scheduled on Monday
        if day == "Senin" and f_pegawai_id in dosen_data:
            jabatan = dosen_data[f_pegawai_id].get("jabatan", "").strip()
            if jabatan:  # Non-empty `jabatan` indicates "tugas tambahan"
                penalties += 20

        # Track room and dosen usage
        dosen_time_usage.setdefault(f_pegawai_id, set()).add(time_slot)
        room_time_usage.setdefault(room_id, set()).add(time_slot)

    return -penalties



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
best_schedule_df.to_csv("./datas/BestSchedule.csv", index=False)

# Display results
print(f"Genetic Algorithm completed in {end_time - start_time:.2f} seconds")
print(f"Best Fitness Score: {best_fitness}")
print(f"Fitness Percentage: {fitness_percentage:.2f}%")
print("Best schedule saved to './datas/BestSchedule.csv'")