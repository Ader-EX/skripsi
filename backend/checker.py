import pandas as pd

# Load the schedule data
file_path = "./datas/BestSchedule.csv"  # Update this with the correct path to your file
schedule_df = pd.read_csv(file_path)

# Parse the 'Jadwal Pertemuan' column into separate day, time, and room columns
schedule_df[['Day', 'Time', 'Room']] = schedule_df['Jadwal Pertemuan'].str.extract(r'(\w+) - ([\d:]+ - [\d:]+) \((.*?)\)')

# Conflict Checker
def check_conflicts(schedule_df):
    conflicts = []

    # Group by day and time to check conflicts for both lecturer and room
    grouped = schedule_df.groupby(['Day', 'Time'])

    for (day, time), group in grouped:
        # Check for lecturer conflicts
        lecturer_conflicts = group[group.duplicated(subset='Dosen', keep=False)]
        for _, row in lecturer_conflicts.iterrows():
            conflicts.append({
                "Conflict Type": "Lecturer Conflict",
                "Details": f"Lecturer {row['Dosen']} is scheduled for multiple classes at the same time.",
                "Day": day,
                "Time": time,
                "Room": row['Room'],
                "Matakuliah": row['Matakuliah'],
                "Class": row['Kelas']
            })

        # Check for room conflicts
        room_conflicts = group[group.duplicated(subset='Room', keep=False)]
        for _, row in room_conflicts.iterrows():
            conflicts.append({
                "Conflict Type": "Room Conflict",
                "Details": f"Room {row['Room']} is scheduled for multiple classes at the same time.",
                "Day": day,
                "Time": time,
                "Room": row['Room'],
                "Matakuliah": row['Matakuliah'],
                "Class": row['Kelas']
            })

    # Convert conflicts to a DataFrame
    conflicts_df = pd.DataFrame(conflicts)
    return conflicts_df

# Run the conflict checker
conflicts_df = check_conflicts(schedule_df)

# Save conflicts to a file
output_path = "./Schedule_Conflicts.csv"
conflicts_df.to_csv(output_path, index=False)

print(f"Conflicts have been saved to {output_path}")
