import pandas as pd

# Load the Ruangan.csv file
ruangan_df = pd.read_csv('./datas/Ruangan.csv')

# Combine duplicates by grouping by `f_koderuang` and aggregating
ruangan_df_cleaned = ruangan_df.groupby('f_koderuang').agg({
    'f_ruang_id': 'first',  # Take the first ID (doesn't matter which)
    'f_namaruang': 'first',  # Take the first name
    'f_tiperuangan': lambda x: ','.join(sorted(set(x))),  # Combine and deduplicate types
    'f_jenisruang_id': 'first',  # Take the first value
    'f_kapasitas_kuliah': 'first',  # Take the first capacity
    'f_statusaktif_penggunaan': 'first',  # Take the first value
    'f_shareprogdi': 'first',  # Take the first value
    'f_alamatruang': 'first',  # Take the first address
    'f_koderuang_mapping': 'first',  # Take the first mapping
}).reset_index()

# Save the cleaned data to a new CSV file (optional)
ruangan_df_cleaned.to_csv('./datas/CleanedRuangan.csv', index=False)

# Check the result
print(ruangan_df_cleaned)