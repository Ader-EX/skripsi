import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import engine
from model.matakuliah_model import MataKuliah

# Read the CSV file
df = pd.read_csv('datas/merged.csv')

# Print the column names to verify
print(df.columns)


# Map CSV columns to Matakuliah model attributes
df.columns = [
    'kodemk', 'namamk', 'sks', 'smt', 'kurikulum', 
    'status_mk', 'kelas', 'tipe_mk'
]

# Print the first few rows to verify the data
print(df.head())

# Insert data into the database
with Session(engine) as session:
    for _, row in df.iterrows():
        matakuliah = MataKuliah(
            kodemk=row['kodemk'],
            namamk=row['namamk'],
            sks=row['sks'],
            smt=row['smt'],
            kurikulum=row['kurikulum'],
            status_mk=row['status_mk'],
            kelas=row['kelas'],
            tipe_mk=row['tipe_mk']
        )
        try:
            session.add(matakuliah)
            session.commit()
        except IntegrityError:
            session.rollback()
            print(f"Duplicate entry found for kodemk: {row['kodemk']}, skipping...")

print("Data insertion completed.")