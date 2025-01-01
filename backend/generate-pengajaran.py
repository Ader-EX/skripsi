import csv
import random

# Sample data for dosens and mata kuliah
f_pegawai_ids = [
    5149, 5150, 5151, 2995, 1041, 5850, 3635, 3044, 2747, 4737, 225, 4687, 2026, 4569, 3911, 3913, 3914, 3883, 3882, 4722,
    584, 4700, 1043, 1050, 585, 2287, 399, 402, 1507, 4958, 5396
]
mata_kuliah = [
    "INF124201", "INF124205", "INF124210", "INF124209", "INF124206", "INF124202", "INF124208", "INF124204",
    "INF124207", "INF124203", "INF124404", "INF124401", "INF124406", "INF124413", "INF124411", "INF124409",
    "INF124412", "INF124407", "INF124402", "INF124408", "INF124405", "INF124403", "INF124410", "INF124639",
    "INF124637", "INF124612", "INF124631", "INF124642", "INF124624", "INF124630", "INF124603", "INF124623",
    "INF124618", "INF124636", "INF124611", "INF124634", "INF124602", "INF124633", "INF124621", "INF124628",
    "INF124614", "INF124613", "INF124622", "INF124629", "INF124625", "INF124632", "INF124601", "INF124641",
    "INF124619", "INF124638", "INF124615", "INF124610", "INF124635", "INF124617", "INF124620", "INF124616",
    "INF124640", "INF124701", "INF124801", "INF124501", "INF124504", "POL124501", "INF124505", "HKM124701",
    "INF124502", "INFMBKM02", "MNJ124305", "SDT124307", "INF124506", "TKM120407", "SIM124109", "INF124503",
    "INF124507"
]

# Generate random pengajaran data
pengajaran_data = []
pengajaran_id = 1

for mk in mata_kuliah:
    # Assign a dosen besar
    dosen_besar = random.choice(f_pegawai_ids)
    pengajaran_data.append([pengajaran_id, dosen_besar, mk, True])  # dosen besar is_dosen_kb=True
    pengajaran_id += 1

    # Assign random dosen kecil (0-2 dosen kecil per mata kuliah)
    dosen_kecil_count = random.randint(0, 2)
    dosen_kecil_ids = random.sample([d for d in f_pegawai_ids if d != dosen_besar], dosen_kecil_count)
    for dosen_kecil in dosen_kecil_ids:
        pengajaran_data.append([pengajaran_id, dosen_kecil, mk, False])  # dosen kecil is_dosen_kb=False
        pengajaran_id += 1

# Write to CSV
output_file = "./datas/pengajaran.csv"
with open(output_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["pengajaran_id", "dosen_id", "mk_id", "is_dosen_kb"])
    writer.writerows(pengajaran_data)

print(f"Generated pengajaran CSV at {output_file}")
