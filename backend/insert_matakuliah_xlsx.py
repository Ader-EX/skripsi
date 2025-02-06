import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from model.matakuliah_model import MataKuliah
from model.programstudi_model import ProgramStudi

# Path to the Excel file
xlsx_file_path = "datas/merge/S1IF.xlsx"

def determine_tipe_and_kelas_besar(nama_mk):
    """
    Determines the tipe_mk and have_kelas_besar based on the course name.
    If "Praktikum" is in the name, tipe_mk is "P" and have_kelas_besar is False.
    Otherwise, tipe_mk is "T" and have_kelas_besar is True.
    """
    if "praktikum" in nama_mk.lower():
        return "P", False
    return "T", True

def load_xlsx_to_database(file_path, program_studi_name):
    duplicates = []

    session = SessionLocal()

    try:
        # Get the Program Studi from the database
        program_studi = session.query(ProgramStudi).filter_by(name=program_studi_name).first()
        if not program_studi:
            raise ValueError(f"Program Studi '{program_studi_name}' not found in the database.")

        # Read the Excel file
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            kodemk = f"IF-{row['f_kodemk']}"  # Prefix kodemk with IF-

            # Check if the MataKuliah already exists **WITH THE SAME PROGRAM STUDI**
            existing_mata_kuliah = session.query(MataKuliah).filter_by(
                kodemk=kodemk, 
                program_studi_id=program_studi.id
            ).first()

            if existing_mata_kuliah:
                duplicates.append(row.to_dict())
                continue  # Skip duplicates

            # If MataKuliah doesn't exist, create it
            tipe_mk, have_kelas_besar = determine_tipe_and_kelas_besar(row["f_namamk"])
            mata_kuliah = MataKuliah(
                kodemk=kodemk,
                namamk=row["f_namamk"],
                sks=row["f_sks_kurikulum"],
                smt=row["f_semester"],
                kurikulum=row["f_kurikulum"],
                status_mk=row["f_statusaktifmk"],
                tipe_mk=tipe_mk,  # Fix: Use the correct "T" or "P"
                have_kelas_besar=have_kelas_besar,
                program_studi_id=program_studi.id  # ✅ Direct association to Program Studi
            )
            session.add(mata_kuliah)

        # Commit changes
        session.commit()

        # Log duplicates
        if duplicates:
            print("Duplicate courses found:")
            for dup in duplicates:
                print(dup)

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the loader for S1IF
load_xlsx_to_database(xlsx_file_path, "S1IF")