import pandas as pd
import numpy as np

# File paths
mata_kuliah_file_path = './datas/MataKuliah.csv'
dosen_file_path = './datas/Dosen.csv'
output_pengajaran_csv = './datas/fixed_pengajaran.csv'

# Load data
mata_kuliah_df = pd.read_csv(mata_kuliah_file_path)
dosen_df = pd.read_csv(dosen_file_path)

# Standardize columns
mata_kuliah_df["Kodemk"] = mata_kuliah_df["Kodemk"].astype(str).str.strip()
mata_kuliah_df["kelas"] = mata_kuliah_df["kelas"].fillna("A")
dosen_df["f_pegawai_id"] = dosen_df["f_pegawai_id"].astype(str).str.strip()

# Randomly assign is_dosen_kb (approximately 20% of dosen will be KB)
np.random.seed(42)  # for reproducibility
dosen_df["is_dosen_kb"] = np.random.choice([True, False], size=len(dosen_df), p=[0.2, 0.8])

pengajaran_data = []
current_pengajaran_id = 1

for _, mk_row in mata_kuliah_df.iterrows():
    mk_id = mk_row["Kodemk"]
    available_classes = list(mk_row["kelas"].strip())

    # Randomly decide if this course will have a KB (50% chance)
    has_kb = np.random.choice([True, False])

    if has_kb:
        # Try to assign a KB dosen
        dosen_kb = dosen_df[dosen_df["is_dosen_kb"]].sample(n=1)
        if not dosen_kb.empty:
            dosen_kb_id = dosen_kb.iloc[0]["f_pegawai_id"]
            # Add entries for all classes with same pengajaran_id
            for class_label in available_classes:
                pengajaran_data.append({
                    "pengajaran_id": current_pengajaran_id,
                    "dosen_id": dosen_kb_id,
                    "mk_id": mk_id,
                    "is_dosen_kb": True,
                    "class": class_label
                })
            current_pengajaran_id += 1

    # Assign regular dosen (2 per class)
    for class_label in available_classes:
        # Get 2 random regular dosen for this class
        regular_dosen = dosen_df[~dosen_df["is_dosen_kb"]].sample(n=2)
        for _, dosen_row in regular_dosen.iterrows():
            pengajaran_data.append({
                "pengajaran_id": current_pengajaran_id,
                "dosen_id": dosen_row["f_pegawai_id"],
                "mk_id": mk_id,
                "is_dosen_kb": False,
                "class": class_label
            })
            current_pengajaran_id += 1

# Convert to DataFrame and save
pengajaran_df = pd.DataFrame(pengajaran_data)
pengajaran_df.to_csv(output_pengajaran_csv, index=False)

print(f"Generated pengajaran CSV saved to {output_pengajaran_csv}")