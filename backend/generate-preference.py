import csv
import random
from datetime import datetime, timedelta

# Sample f_pegawai_ids
f_pegawai_ids = [
    5149, 5150, 5151, 2995, 1041, 5850, 3635, 3044, 2747, 4737, 225, 4687, 2026, 4569, 3911, 3913, 3914, 3883, 3882, 4722,
    584, 4700, 1043, 1050, 585, 2287, 399, 402, 1507, 4958, 5396
]

# Possible days
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Generate time slots
def generate_time_slots():
    slots = []
    start_time = datetime.strptime("07:00", "%H:%M")
    end_time = datetime.strptime("12:00", "%H:%M")
    interval = timedelta(minutes=50)

    # Morning slots
    while start_time < end_time:
        slots.append((start_time.strftime("%H:%M"), (start_time + interval).strftime("%H:%M")))
        start_time += interval

    # Afternoon slots
    start_time = datetime.strptime("13:00", "%H:%M")
    end_time = datetime.strptime("18:00", "%H:%M")
    while start_time < end_time:
        slots.append((start_time.strftime("%H:%M"), (start_time + interval).strftime("%H:%M")))
        start_time += interval

    return slots

time_slots = generate_time_slots()

# Generate random preferences
preferences = []
for f_pegawai_id in f_pegawai_ids:
    num_preferences = random.randint(2, 5)  # Each lecturer can have 2-5 preferences
    for _ in range(num_preferences):
        day = random.choice(days)
        start_time, end_time = random.choice(time_slots)
        high_preference = random.choice([True, False])  # Random high preference
        preferences.append([f_pegawai_id, day, start_time, end_time, high_preference])

# Write to CSV
output_file = "./datas/lecturer_time_preferences.csv"
with open(output_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["f_pegawai_id", "day", "start_time", "end_time", "high_preference"])
    writer.writerows(preferences)

print(f"Generated lecturer time preferences CSV at {output_file}")
