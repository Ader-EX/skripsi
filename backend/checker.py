import pandas as pd

def check_schedule_conflicts(schedule_file, dosen_file, ruangan_file):
    # Load the schedule and reference data
    schedule_df = pd.read_csv(schedule_file)
    dosen_df = pd.read_csv(dosen_file)
    ruangan_df = pd.read_csv(ruangan_file)
    
    # Ensure `jabatan` is treated as a string
    dosen_df['jabatan'] = dosen_df['jabatan'].fillna("").astype(str).str.strip()
    dosen_data = dosen_df.set_index('f_pegawai_id').to_dict(orient='index')
    
    # Conflict dictionaries
    lecturer_conflicts = []
    room_conflicts = []
    tugas_tambahan_conflicts = []
    
    # Track usage
    lecturer_time_slots = {}
    room_time_slots = {}
    
    # Iterate through schedule
    for _, row in schedule_df.iterrows():
        f_pegawai_id = str(row["Dosen ID"]).strip()
        room_id = row["Jadwal Pertemuan"].split('(')[1][:-1]
        day = row["Jadwal Pertemuan"].split(" - ")[0]
        time_slot = row["Jadwal Pertemuan"].split(" - ")[1]
        
        # Check for duplicate lecturer time slots
        if f_pegawai_id not in lecturer_time_slots:
            lecturer_time_slots[f_pegawai_id] = set()
        if time_slot in lecturer_time_slots[f_pegawai_id]:
            lecturer_conflicts.append({
                "Dosen ID": f_pegawai_id,
                "Dosen Name": dosen_data.get(f_pegawai_id, {}).get("f_namapegawai", "Unknown"),
                "Time Slot": time_slot,
                "Conflict": "Duplicate lecturer time slot"
            })
        lecturer_time_slots[f_pegawai_id].add(time_slot)
        
        # Check for duplicate room time slots
        if room_id not in room_time_slots:
            room_time_slots[room_id] = set()
        if time_slot in room_time_slots[room_id]:
            room_conflicts.append({
                "Room ID": room_id,
                "Time Slot": time_slot,
                "Conflict": "Duplicate room time slot"
            })
        room_time_slots[room_id].add(time_slot)
        
        # Check for lecturers with tugas tambahan on Monday
        if day == "Senin" and f_pegawai_id in dosen_data:
            jabatan = dosen_data[f_pegawai_id].get("jabatan", "").strip()
            if jabatan:  # Non-empty `jabatan` indicates "tugas tambahan"
                tugas_tambahan_conflicts.append({
                    "Dosen ID": f_pegawai_id,
                    "Dosen Name": dosen_data[f_pegawai_id].get("f_namapegawai", "Unknown"),
                    "Day": day,
                    "Conflict": "Tugas tambahan scheduled on Monday"
                })
    
    # Combine all conflicts into one DataFrame
    all_conflicts = pd.DataFrame(
        lecturer_conflicts + room_conflicts + tugas_tambahan_conflicts
    )
    
    return all_conflicts


if __name__ == "__main__":
    # Paths to the schedule and reference data files
    schedule_file = "./datas/BestSchedule.csv"
    dosen_file = "./datas/Dosen.csv"
    ruangan_file = "./datas/CleanedRuangan.csv"
    
    # Check for conflicts
    conflicts = check_schedule_conflicts(schedule_file, dosen_file, ruangan_file)
    
    # Output conflicts to a CSV file
    if not conflicts.empty:
        conflicts.to_csv("./datas/ScheduleConflicts.csv", index=False)
        print("Conflicts found! Saved to './datas/ScheduleConflicts.csv'.")
    else:
        print("No conflicts found in the schedule.")
