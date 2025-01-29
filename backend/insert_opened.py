import pandas as pd
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from model.matakuliah_programstudi import MataKuliahProgramStudi
from model.openedclass_model import OpenedClass

# Set up logging
logging.basicConfig(
    filename="openedclass_duplicates.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def determine_capacity(nama_mk: str) -> int:
    """
    Determines the capacity of a class based on the course name.
    If "Praktikum" is in the name, return 40 (practical class).
    Otherwise, return 45 (theory class).
    """
    if "praktikum" in nama_mk.lower():
        return 40
    return 45

def insert_opened_classes(file_path, program_studi_id):
    """
    Reads the Excel file and inserts unique entries into the OpenedClass table
    by comparing each row with the previous one.
    """
    session = SessionLocal()
    inserted_rows = []
    duplicates = []

    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        logging.info(f"Successfully read Excel file: {file_path}")

        # Track the last processed row
        last_kodemk = None
        last_kelas = None

        for index, row in df.iterrows():
            try:
                # Remove 'IF-' prefix from `f_kodemk`
                kodemk = row["f_kodemk"]
                if kodemk.startswith("IF-"):
                    kodemk = kodemk[3:]  # Remove 'IF-' prefix

                # Normalize class name
                kelas = row["f_kelas"].strip().upper()

                # Check if the current row matches the previous one
                if kodemk == last_kodemk and kelas == last_kelas:
                    logging.info(f"Skipping duplicate row for kodemk={kodemk}, kelas={kelas}")
                    duplicates.append({"kodemk": kodemk, "kelas": kelas})
                    continue

                logging.debug(f"Processing row {index + 1}: kodemk={kodemk}, kelas={kelas}")

                # Find the matching MataKuliahProgramStudi entry
                logging.debug(f"Querying MataKuliahProgramStudi with mata_kuliah_id={kodemk} and program_studi_id={program_studi_id}")
                mps_entry = session.query(MataKuliahProgramStudi).filter_by(
                    mata_kuliah_id=kodemk,
                    program_studi_id=program_studi_id
                ).first()

                if not mps_entry:
                    logging.warning(f"No matching MataKuliahProgramStudi found for kodemk={kodemk} and program_studi_id={program_studi_id}")
                    continue

                # Determine capacity based on course name
                kapasitas = determine_capacity(row["f_namamk"])
                logging.debug(f"Determined capacity for kodemk={kodemk}, kelas={kelas}: {kapasitas}")

                # Check for existing OpenedClass entry in the database
                existing_class = session.query(OpenedClass).filter_by(
                    mata_kuliah_program_studi_id=mps_entry.id,
                    kelas=kelas
                ).first()

                if existing_class:
                    logging.info(f"Duplicate OpenedClass found in database for kodemk={kodemk}, kelas={kelas}")
                    duplicates.append({"kodemk": kodemk, "kelas": kelas})
                    continue

                # Create a new OpenedClass entry
                new_opened_class = OpenedClass(
                    mata_kuliah_program_studi_id=mps_entry.id,
                    kelas=kelas,
                    kapasitas=kapasitas
                )
                session.add(new_opened_class)
                inserted_rows.append({"kodemk": kodemk, "kelas": kelas, "kapasitas": kapasitas})
                logging.info(f"Inserted OpenedClass: kodemk={kodemk}, kelas={kelas}, kapasitas={kapasitas}")

                # Update the last processed row
                last_kodemk = kodemk
                last_kelas = kelas

            except Exception as row_error:
                logging.error(f"Error processing row {index + 1}: {row_error}")
                session.rollback()  # Rollback the session for the current row

        # Commit changes
        session.commit()
        logging.info(f"Successfully committed changes. Inserted {len(inserted_rows)} rows, skipped {len(duplicates)} duplicates.")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()

# Run the function
insert_opened_classes("datas/openedclass/S1IF.xlsx", 1)