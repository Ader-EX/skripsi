import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
from collections import Counter
from database import SessionLocal
from model.pengajaran_model import Pengajaran
from model.openedclass_model import OpenedClass

# Path to the Excel file
xlsx_file_path = "datas/openedclass/S1SI_updated.xlsx"

def determine_roles_for_kodemk(dosen_counts, dosen_id):
    """
    Assigns roles based on the highest count.
    - If the dosen_id has the highest count, assign "besar".
    - Otherwise, assign "kecil".
    """
    max_count = max(dosen_counts.values())
    if dosen_counts[dosen_id] == max_count:
        return ["besar"]
    return ["kecil"]

def load_xlsx_to_database(file_path):
    session = SessionLocal()
    try:
        # Read the Excel file
        df = pd.read_excel(file_path)

        # Group data by kodemk
        grouped = df.groupby("f_kodemk")

        for kodemk, group in grouped:
            # Count appearances of each dosen_id for the current kodemk
            dosen_counts = Counter(group["dosen_id"])

            for _, row in group.iterrows():
                dosen_id = row["dosen_id"]
                kelas = row["f_kelas"]
                nama_mk = row["f_namamk"]

                # Extract the opened_class_id
                opened_class = (
                    session.query(OpenedClass)
                    .filter(OpenedClass.kelas == kelas)
                    .join(OpenedClass.mata_kuliah_program_studi)
                    .filter(OpenedClass.mata_kuliah_program_studi.mata_kuliah_id == kodemk)
                    .first()
                )

                if not opened_class:
                    print(f"OpenedClass not found for kodemk={kodemk} and kelas={kelas}")
                    continue

                opened_class_id = opened_class.id

                # Determine roles for the lecturer
                roles = determine_roles_for_kodemk(dosen_counts, dosen_id)

                # Check if the Pengajaran entry already exists
                existing_entry = (
                    session.query(Pengajaran)
                    .filter_by(dosen_id=dosen_id, opened_class_id=opened_class_id)
                    .first()
                )
                if existing_entry:
                    print(f"Duplicate found for dosen_id={dosen_id}, opened_class_id={opened_class_id}")
                    continue

                # Insert into Pengajaran
                pengajaran = Pengajaran(
                    dosen_id=dosen_id,
                    opened_class_id=opened_class_id,
                    roles=roles
                )
                session.add(pengajaran)

        # Commit all changes
        session.commit()

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

# Run the loader for the file
load_xlsx_to_database(xlsx_file_path)
