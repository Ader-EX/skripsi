import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from model.matakuliah_model import MataKuliah
from model.programstudi_model import ProgramStudi
from model.matakuliah_model import mata_kuliah_program_studi

# Path to the Excel file
xlsx_file_path = "datas/merge/S1SI.xlsx"

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

    # Use SessionLocal from database.py
    session = SessionLocal()

    try:
        # Get the program_studi ID from the database
        program_studi = session.query(ProgramStudi).filter_by(name=program_studi_name).first()
        if not program_studi:
            raise ValueError(f"Program Studi '{program_studi_name}' not found in the database.")

        program_studi_id = program_studi.id

        # Read the Excel file
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            kodemk = row["f_kodemk"]

            # Check if the MataKuliah already exists
            mata_kuliah = session.query(MataKuliah).filter_by(kodemk=kodemk).first()

            if not mata_kuliah:
                # If MataKuliah doesn't exist, create it
                tipe_mk, have_kelas_besar = determine_tipe_and_kelas_besar(row["f_namamk"])
                mata_kuliah = MataKuliah(
                    kodemk=kodemk,
                    namamk=row["f_namamk"],
                    sks=row["f_sks_kurikulum"],
                    smt=row["f_semester"],
                    kurikulum=row["f_kurikulum"],
                    status_mk=row["f_statusaktifmk"],
                    tipe_mk=tipe_mk,
                    have_kelas_besar=have_kelas_besar
                )
                session.add(mata_kuliah)
                session.commit()  # Commit to save the MataKuliah first

            # Check if the association with the program_studi already exists
            association_exists = session.execute(
                mata_kuliah_program_studi.select().where(
                    (mata_kuliah_program_studi.c.mata_kuliah_id == mata_kuliah.kodemk) &
                    (mata_kuliah_program_studi.c.program_studi_id == program_studi_id)
                )
            ).first()

            if association_exists:
                duplicates.append(row.to_dict())
                continue

            # Add the association to the mata_kuliah_program_studi table
            session.execute(
                mata_kuliah_program_studi.insert().values(
                    mata_kuliah_id=mata_kuliah.kodemk,
                    program_studi_id=program_studi_id
                )
            )

        # Commit the session to save changes to the database
        session.commit()

        # Log duplicates
        if duplicates:
            print("Duplicate associations found:")
            for dup in duplicates:
                print(dup)

    except Exception as e:
        print("Error occurred:", e)
        session.rollback()
    finally:
        session.close()

# Run the loader for D3SI
load_xlsx_to_database(xlsx_file_path, "S1SI")
