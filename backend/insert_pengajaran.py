import pandas as pd
import logging
from collections import Counter
from sqlalchemy.orm import Session
from database import SessionLocal
from model.pengajaran_model import Pengajaran
from model.openedclass_model import OpenedClass
from model.matakuliah_programstudi import MataKuliahProgramStudi

# Path to the Excel file
xlsx_file_path = "datas/openedclass/S1SI_updated.xlsx"

# Set up logging
logging.basicConfig(
    filename="pengajaran_errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def remove_prefix(kodemk):
    """Remove the 'SI-' prefix from kodemk if it exists."""
    return kodemk[3:] if kodemk.startswith("SI-") else kodemk

def determine_roles(dosen_counts, dosen_id):
    """
    Determine roles for dosen_id based on the highest count.
    - "besar" for the most frequent dosen_id
    - "kecil" otherwise
    """
    max_count = max(dosen_counts.values())
    return ["besar"] if dosen_counts[dosen_id] == max_count else ["kecil"]

def process_pengajaran(file_path, program_studi_id):
    session = SessionLocal()
    try:
        # Read Excel data
        print("Reading Excel data...")
        df = pd.read_excel(file_path)

        # Remove the 'SI-' prefix from f_kodemk
        print("Removing 'SI-' prefix from f_kodemk...")
        df["f_kodemk"] = df["f_kodemk"].apply(remove_prefix)

        # Ensure dosen_id exists
        if "dosen_id" not in df.columns:
            raise ValueError("Column 'dosen_id' not found in Excel file.")

        print(f"Data contains {len(df)} rows.")

        # Group data by f_kodemk (to assign roles within the same kodemk)
        grouped = df.groupby("f_kodemk")

        for kodemk, group in grouped:
            print(f"\nProcessing kodemk: {kodemk} with {len(group)} rows...")
            dosen_counts = Counter(group["dosen_id"])  # Count occurrences for roles

            for _, row in group.iterrows():
                try:
                    dosen_id = row["dosen_id"]
                    kelas = row["f_kelas"]

                    # Step 1: Find mata_kuliah_program_studi_id filtered by program_studi_id
                    print(f"Looking up MataKuliahProgramStudi for mata_kuliah_id={kodemk}, program_studi_id={program_studi_id}...")
                    mata_kuliah_program_studi = (
                        session.query(MataKuliahProgramStudi)
                        .filter_by(mata_kuliah_id=kodemk, program_studi_id=program_studi_id)
                        .first()
                    )

                    if not mata_kuliah_program_studi:
                        print(f"ERROR: No MataKuliahProgramStudi found for kodemk={kodemk}, program_studi_id={program_studi_id}. Skipping row.")
                        logging.warning(f"No MataKuliahProgramStudi found for kodemk={kodemk}, program_studi_id={program_studi_id}.")
                        continue

                    mata_kuliah_program_studi_id = mata_kuliah_program_studi.id
                    print(f"Found MataKuliahProgramStudi with id={mata_kuliah_program_studi_id}.")

                    # Step 2: Find opened_class_id
                    print(f"Looking up OpenedClass for mata_kuliah_program_studi_id={mata_kuliah_program_studi_id} and kelas={kelas.strip()}...")
                    opened_class = (
                        session.query(OpenedClass)
                        .filter(
                            OpenedClass.mata_kuliah_program_studi_id == mata_kuliah_program_studi_id,
                            OpenedClass.kelas == kelas.strip()
                        )
                        .first()
                    )

                    if not opened_class:
                        print(f"ERROR: No OpenedClass found for kodemk={kodemk}, kelas={kelas.strip()}, mata_kuliah_program_studi_id={mata_kuliah_program_studi_id}.")
                        logging.warning(f"No OpenedClass found for kodemk={kodemk}, kelas={kelas.strip()}, mata_kuliah_program_studi_id={mata_kuliah_program_studi_id}.")
                        continue

                    opened_class_id = opened_class.id
                    print(f"Found OpenedClass with id={opened_class_id}.")

                    # Step 3: Determine roles
                    roles = determine_roles(dosen_counts, dosen_id)
                    print(f"Assigned roles for dosen_id={dosen_id}: {roles}.")

                    # Step 4: Check for duplicates and insert Pengajaran
                    print(f"Checking for existing Pengajaran entry with dosen_id={dosen_id}, opened_class_id={opened_class_id}...")
                    existing_entry = (
                        session.query(Pengajaran)
                        .filter_by(dosen_id=dosen_id, opened_class_id=opened_class_id)
                        .first()
                    )

                    if existing_entry:
                        print(f"Duplicate found for dosen_id={dosen_id}, opened_class_id={opened_class_id}. Skipping insertion.")
                        logging.info(f"Duplicate found for dosen_id={dosen_id}, opened_class_id={opened_class_id}.")
                        continue

                    print(f"Inserting new Pengajaran entry for dosen_id={dosen_id}, opened_class_id={opened_class_id}...")
                    pengajaran = Pengajaran(
                        dosen_id=dosen_id,
                        roles=roles,
                        opened_class_id=opened_class_id,
                    )
                    session.add(pengajaran)
                    session.commit()  # Commit after each successful insert

                except Exception as row_error:
                    print(f"Error processing row {row}: {row_error}")
                    logging.error(f"Error processing row {row}: {row_error}")
                    session.rollback()  # Rollback the session for the current row

    except Exception as e:
        print(f"Error occurred: {e}")
        logging.error(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()


# Specify the file path and program_studi_id
file_path = "datas/openedclass/S1SI_updated.xlsx"
program_studi_id = 2

# Call the function
process_pengajaran(file_path, program_studi_id)