import random
from datetime import datetime, timedelta
import pandas as pd
import time

# Load the data
mata_kuliah_df = pd.read_csv("./datas/MataKuliah.csv")
dosen_df = pd.read_csv("./datas/dosen.csv")
ruangan_df = pd.read_csv("./datas/Ruangan.csv")

# Preprocess room and course data for quick lookups
room_types = ruangan_df.set_index("f_koderuang")["f_tiperuangan"].to_dict()
course_types = mata_kuliah_df.set_index("Kodemk")["tipe_MK"].to_dict()


classes = ["A", "B", "C", "D"] 


def generate_pengajaran_table():
    pengajaran = []
    for _, row in mata_kuliah_df.iterrows():
        mata_kuliah_id = row["Kodemk"]
        mata_kuliah_name = row["Namamk"]
        is_kelas_besar = row.get("is_kelas_besar", False)  # Add column `is_kelas_besar` in MataKuliah

        if is_kelas_besar:
            # Assign multiple dosen for Kelas Besar
            dosen_besar = random.sample(dosen_df["f_pegawai_id"].tolist(), k=2)  # Randomly select 2 dosen besar
            for dosen_id in dosen_besar:
                pengajaran.append({
                    "mata_kuliah_id": mata_kuliah_id,
                    "mata_kuliah_name": mata_kuliah_name,
                    "class": "Kelas Besar",
                    "dosen_id": dosen_id,
                    "role": "Dosen Besar"  # Mark as Dosen Besar
                })

            # Assign dosen kecil to sub-classes A, B, C, D...
            for sub_class in classes:
                dosen_kecil = random.choice(dosen_df["f_pegawai_id"].tolist())  # Randomly select a dosen kecil
                pengajaran.append({
                    "mata_kuliah_id": mata_kuliah_id,
                    "class": sub_class,
                    "dosen_id": dosen_kecil,
                    "role": "Dosen Kecil"  # Mark as Dosen Kecil
                })
        else:
            # For regular classes, assign one dosen
            dosen_id = random.choice(dosen_df["f_pegawai_id"].tolist())
            pengajaran.append({
                "mata_kuliah_id": mata_kuliah_id,
                "class": "Regular",
                "dosen_id": dosen_id,
                "role": "Dosen"
            })

    return pd.DataFrame(pengajaran)
pengajaran_table = generate_pengajaran_table()
pengajaran_table.to_csv("Pengajaran.csv", index=False)
print("Pengajaran table generated and saved.")

# Generate adjusted time slots (Monday-Friday, 07:00-18:00, with break 12:00-13:00)
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


def schedule_kelas_besar(pengajaran_table, adjusted_time_slots):
    schedule = []
    kelas_besar_courses = pengajaran_table[pengajaran_table["class"] == "Kelas Besar"]["mata_kuliah_id"].unique()

    for course_id in kelas_besar_courses:
        # Get dosen besar and their assigned time slots
        dosen_besar = pengajaran_table[
            (pengajaran_table["mata_kuliah_id"] == course_id) &
            (pengajaran_table["role"] == "Dosen Besar")
        ]["f_pegawai_id"].tolist()

        time_slot = random.choice(adjusted_time_slots)
        for dosen_id in dosen_besar:
            schedule.append({
                "Course ID": course_id,
                "Class": "Kelas Besar",
                "Dosen ID": dosen_id,
                "Day": time_slot["day"],
                "Start Time": time_slot["start_time"],
                "End Time": time_slot["end_time"]
            })

        # Assign the same schedule to all sub-classes
        sub_classes = pengajaran_table[
            (pengajaran_table["mata_kuliah_id"] == course_id) &
            (pengajaran_table["role"] == "Dosen Kecil")
        ]
        for _, sub_class in sub_classes.iterrows():
            schedule.append({
                "Course ID": course_id,
                "Class": sub_class["class"],
                "Dosen ID": sub_class["f_pegawai_id"],
                "Day": time_slot["day"],
                "Start Time": time_slot["start_time"],
                "End Time": time_slot["end_time"]
            })

    return pd.DataFrame(schedule)

# Generate schedules
kelas_besar_schedule = schedule_kelas_besar(pengajaran_table, adjusted_time_slots)
kelas_besar_schedule.to_csv("KelasBesarSchedule.csv", index=False)
print("Kelas Besar schedules generated and saved.")

# Assign random courses to dosen
dosen_to_courses = {}
available_courses = mata_kuliah_df["Kodemk"].tolist()
for _, row in dosen_df.iterrows():
    dosen_to_courses[row['f_pegawai_id']] = random.sample(
        available_courses, k=min(3, len(available_courses))  # Adjust number of courses dynamically
    )


def calculate_fitness_with_kelas_besar(schedule):
    penalties = 0
    dosen_time_usage = {}
    room_time_usage = {}
    kelas_besar_schedules = {}

    for entry in schedule:
        dosen_id = entry["Dosen ID"]
        room_id = entry["Room ID"]
        time_slot_id = entry["Time Slot ID"]
        course_id = entry["Course ID"]
        class_type = entry["Class"]

        # Track schedules for Kelas Besar
        if class_type == "Kelas Besar":
            if course_id not in kelas_besar_schedules:
                kelas_besar_schedules[course_id] = time_slot_id
            elif kelas_besar_schedules[course_id] != time_slot_id:
                penalties += 10  # Penalty for inconsistent Kelas Besar schedule

        # Penalty 1: Dosen and room conflicts
        if time_slot_id in dosen_time_usage.get(dosen_id, set()):
            penalties += 10
        if time_slot_id in room_time_usage.get(room_id, set()):
            penalties += 10

        # Penalty 2: Room type mismatch
        room_type = room_types.get(room_id, "T")
        course_type = "P" if course_types.get(course_id, 0) == 1 else "T"
        if room_type != course_type:
            penalties += 10

        # Track usage
        dosen_time_usage.setdefault(dosen_id, set()).add(time_slot_id)
        room_time_usage.setdefault(room_id, set()).add(time_slot_id)

    return -penalties


# Fitness function
# def calculate_fitness(schedule):
#     penalties = 0
#     dosen_time_usage = {}
#     room_time_usage = {}
    
#     for entry in schedule:
#         dosen_id = entry["Dosen ID"]
#         room_id = entry["Room ID"]
#         time_slot_id = entry["Time Slot ID"]
#         course_code = entry["Course Code"]

#         # Penalty 1: Dosen and room conflicts
#         if time_slot_id in dosen_time_usage.get(dosen_id, set()):
#             penalties += 10
#         if time_slot_id in room_time_usage.get(room_id, set()):
#             penalties += 10

#         # Penalty 2: Room type mismatch
#         room_type = room_types.get(room_id, "T")  # Default to "T" if not found
#         course_type = "P" if course_types.get(course_code, 0) == 1 else "T"
#         if room_type != course_type:
#             penalties += 10

#         # Penalty 3: Monday restrictions
#         if entry["Day"] == "Monday" and not pd.isna(
#             dosen_df.loc[dosen_df['f_pegawai_id'] == dosen_id, 'jabatan'].values[0]
#         ):
#             penalties += 15

#         # Track usage
#         dosen_time_usage.setdefault(dosen_id, set()).add(time_slot_id)
#         room_time_usage.setdefault(room_id, set()).add(time_slot_id)
    
#     return -penalties  # Higher fitness is better

# Selection function
def select_parents(population, fitness_scores):
    total_fitness = sum(fitness_scores)
    probabilities = [score / total_fitness for score in fitness_scores]
    return random.choices(population, probabilities, k=2)

# Crossover function
def crossover(parent1, parent2):
    point = random.randint(0, len(parent1) - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2

# Mutation function
def mutate(schedule, mutation_rate=0.1):
    for entry in schedule:
        if random.random() < mutation_rate:
            entry["Time Slot ID"] = random.choice(adjusted_time_slots)["time_slot_id"]
    return schedule

# Create initial population

def create_initial_population_with_kelas_besar(population_size):
    population = []
    for _ in range(population_size):
        schedule = []
        for _, row in pengajaran_table.iterrows():
            course_id = row["mata_kuliah_id"]
            class_type = row["class"]
            dosen_id = row["dosen_id"]
            role = row["role"]

            # Assign time slot and room
            time_slot = random.choice(adjusted_time_slots)
            room = random.choice(ruangan_df['f_koderuang'].tolist())

            # Kelas Besar logic
            if class_type == "Kelas Besar":
                # Assign same schedule to all sub-classes
                for sub_class in classes:
                    schedule.append({
                        "Course ID": course_id,
                        "Class": sub_class,
                        "Dosen ID": dosen_id,
                        "Role": role,
                        "Room ID": room,
                        "Time Slot ID": time_slot["time_slot_id"],
                        "Day": time_slot["day"],
                        "Start Time": time_slot["start_time"],
                        "End Time": time_slot["end_time"]
                    })
            else:
                # Regular class or Kelas Kecil
                schedule.append({
                    "Course ID": course_id,
                    "Class": class_type,
                    "Dosen ID": dosen_id,
                    "Role": role,
                    "Room ID": room,
                    "Time Slot ID": time_slot["time_slot_id"],
                    "Day": time_slot["day"],
                    "Start Time": time_slot["start_time"],
                    "End Time": time_slot["end_time"]
                })
        population.append(schedule)
    return population



# def create_initial_population(population_size):
#     population = []
#     for _ in range(population_size):
#         schedule = []
#         for dosen_id, courses in dosen_to_courses.items():
#             dosen_name = dosen_df.loc[dosen_df['f_pegawai_id'] == dosen_id, 'f_namapegawai'].values[0]
#             for course_code in courses:
#                 course_name = mata_kuliah_df.loc[mata_kuliah_df['Kodemk'] == course_code, 'Namamk'].values[0]
#                 time_slot = random.choice(adjusted_time_slots)
#                 room = random.choice(ruangan_df['f_koderuang'].tolist())
#                 schedule.append({
#                     "Dosen ID": dosen_id,
#                     "Dosen Name": dosen_name,  # Add Dosen name here
#                     "Course Code": course_code,
#                     "Course Name": course_name, 
#                     "Room ID": room,
#                     "Time Slot ID": time_slot["time_slot_id"],
#                     "Day": time_slot["day"],
#                     "Start Time": time_slot["start_time"],
#                     "End Time": time_slot["end_time"]
#                 })
#         population.append(schedule)
#     return population


# Genetic Algorithm with Debugging
def genetic_algorithm_with_debug(population, generations=50, mutation_rate=0.1):
    start_time = time.time()
    for generation in range(generations):
        fitness_scores = [calculate_fitness_with_kelas_besar(ind) for ind in population]
        print(f"Generation {generation + 1}/{generations}, Best Fitness: {max(fitness_scores)}, Average Fitness: {sum(fitness_scores) / len(fitness_scores):.2f}")
        new_population = []
        for _ in range(len(population) // 2):
            parent1, parent2 = select_parents(population, fitness_scores)
            child1, child2 = crossover(parent1, parent2)
            new_population.extend([mutate(child1, mutation_rate), mutate(child2, mutation_rate)])
        population = new_population
    end_time = time.time()
    elapsed_time = end_time - start_time
    best_schedule = max(population, key=calculate_fitness_with_kelas_besar)
    print(f"\nOptimization Complete! Best Fitness: {calculate_fitness_with_kelas_besar(best_schedule)}, Time Taken: {elapsed_time:.2f} seconds")
    return best_schedule

# Run Genetic Algorithm
print("Starting Genetic Algorithm...")
population = create_initial_population_with_kelas_besar(10)
optimized_schedule = genetic_algorithm_with_debug(population)
pd.DataFrame(optimized_schedule).to_csv("optimized_algorithm_schedule.csv", index=False)
print("Optimized schedule saved to 'optimized_algorithm_schedule.csv'")
