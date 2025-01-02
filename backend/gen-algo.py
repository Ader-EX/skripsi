import pandas as pd
import random
from datetime import datetime, timedelta

# File paths
mata_kuliah_file_path = './datas/MataKuliah.csv'
pengajaran_file_path = './datas/pengajaran.csv'
ruangan_file_path = './datas/CleanedRuangan.csv'

# Load data
mata_kuliah_df = pd.read_csv(mata_kuliah_file_path)
pengajaran_df = pd.read_csv(pengajaran_file_path)
ruangan_df = pd.read_csv(ruangan_file_path)

# Standardize columns
mata_kuliah_df["Kodemk"] = mata_kuliah_df["Kodemk"].astype(str).str.strip()
pengajaran_df["mk_id"] = pengajaran_df["mk_id"].astype(str).str.strip()
mata_kuliah_df["kelas"] = mata_kuliah_df["kelas"].fillna("A")  # Default class to "A"

# Generate adjusted time slots
def generate_adjusted_time_slots(start_time, end_time, interval_minutes=50):
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
    slots = []
    for day in days:
        current_time = start_time
        while current_time < end_time:
            slot_end_time = current_time + timedelta(minutes=interval_minutes)
            slots.append({
                "day": day,
                "start_time": current_time.strftime("%H:%M"),
                "end_time": slot_end_time.strftime("%H:%M")
            })
            current_time = slot_end_time
    return slots

time_slots = generate_adjusted_time_slots(
    start_time=datetime(2024, 1, 1, 7, 0),
    end_time=datetime(2024, 1, 1, 18, 0)
)

# Generate schedule
def generate_schedule(pengajaran_df, mata_kuliah_df, time_slots):
    schedule = []
    no = 1

    for _, pengajaran_row in pengajaran_df.iterrows():
        mk_id = pengajaran_row["mk_id"]
        dosen_id = pengajaran_row["dosen_id"]
        is_dosen_kb = pengajaran_row["is_dosen_kb"]

        # Fetch Mata Kuliah details
        mata_kuliah = mata_kuliah_df[mata_kuliah_df["Kodemk"] == mk_id]
        if mata_kuliah.empty:
            print(f"[WARNING] mk_id {mk_id} not found in MataKuliah.csv. Skipping.")
            continue

        matakuliah_name = mata_kuliah["Namamk"].values[0]
        kelas_labels = list(mata_kuliah["kelas"].values[0])  # Classes for this lecture
        sks = mata_kuliah["sks"].values[0]
        semester = mata_kuliah["smt"].values[0]

        # Assign a random time slot and room for each class
        for kelas in kelas_labels:
            time_slot = random.choice(time_slots)
            room = random.choice(ruangan_df["f_koderuang"].tolist())
            schedule.append({
                "No": no,
                "Kodemk": mk_id,
                "Matakuliah": matakuliah_name,
                "Kelas": f"Kelas {kelas}",
                "Dosen ID": dosen_id,
                "Is Dosen KB": is_dosen_kb,
                "Day": time_slot["day"],
                "Start Time": time_slot["start_time"],
                "End Time": time_slot["end_time"],
                "Room": room,
                "Sks": sks,
                "Semester": semester
            })
            no += 1

    return pd.DataFrame(schedule)

# Generate and save the schedule
schedule_df = generate_schedule(pengajaran_df, mata_kuliah_df, time_slots)
schedule_df.to_csv("./datas/hasil/SimpleSchedule.csv", index=False)

print("Schedule generated and saved to './datas/hasil/SimpleSchedule.csv'")
