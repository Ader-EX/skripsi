import pandas as pd
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from model.openedclass_model import OpenedClass
from model.matakuliah_programstudi import MataKuliahProgramStudi
from model.dosenopened_model import openedclass_dosen  # Import the association table

# Path to the Excel file

# Set up logging
logging.basicConfig(
    filename="openedclass_dosen_errors.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def remove_prefix(kodemk):
    """Remove the 'IF-' prefix from kodemk if it exists."""
    return kodemk[3:] if kodemk.startswith("IF-") else kodemk

def process_openedclass_dosen(file_path, program_studi_id):
    session = SessionLocal()
    try:
        # Read Excel data
        print("Reading Excel data...")
        df = pd.read_excel(file_path)

        # Remove the 'IF-' prefix from f_kodemk
        print("Removing 'IF-' prefix from f_kodemk...")
        df["f_kodemk"] = df["f_kodemk"].apply(remove_prefix)

        # Ensure dosen_id exists
        if "dosen_id" not in df.columns:
            raise ValueError("Column 'dosen_id' not found in Excel file.")

        print(f"Data contains {len(df)} rows.")

        # Group data by f_kodemk and f_kelas (to handle each class separately)
        grouped = df.groupby(["f_kodemk", "f_kelas"])

        for (kodemk, kelas), group in grouped:
            print(f"\nProcessing kodemk: {kodemk}, kelas: {kelas} with {len(group)} rows...")

            # Step 1: Find mata_kuliah_program_studi_id filtered by program_studi_id
            print(f"Looking up MataKuliahProgramStudi for mata_kuliah_id={kodemk}, program_studi_id={program_studi_id}...")
            mata_kuliah_program_studi = (
                session.query(MataKuliahProgramStudi)
                .filter_by(mata_kuliah_id=kodemk, program_studi_id=program_studi_id)
                .first()
            )

            if not mata_kuliah_program_studi:
                print(f"ERROR: No MataKuliahProgramStudi found for kodemk={kodemk}, program_studi_id={program_studi_id}. Skipping group.")
                logging.warning(f"No MataKuliahProgramStudi found for kodemk={kodemk}, program_studi_id={program_studi_id}.")
                continue

            mata_kuliah_program_studi_id = mata_kuliah_program_studi.id
            print(f"Found MataKuliahProgramStudi with id={mata_kuliah_program_studi_id}.")

            # Step 2: Find opened_class_id
            print(f"Looking up OpenedClass for mata_kuliah_program_studi_id={mata_kuliah_program_studi_id} and kelas={kelas.strip()}...")
            opened_class = (
                session.query(OpenedClass)
                .filter(
                    OpenedClass.mata_kuliah_kodemk == mata_kuliah_program_studi_id,
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

            # Step 3: Insert into openedclass_dosen
            for dosen_id in group["dosen_id"].unique():
                print(f"Inserting into openedclass_dosen: opened_class_id={opened_class_id}, dosen_id={dosen_id}...")
                session.execute(
                    openedclass_dosen.insert().values(
                        opened_class_id=opened_class_id,
                        dosen_id=dosen_id
                    )
                )

            session.commit()  # Commit after processing each group

    except Exception as e:
        print(f"Error occurred: {e}")
        logging.error(f"Error occurred: {e}")
        session.rollback()
    finally:
        session.close()


# Specify the file path and program_studi_id
file_path = "datas/openedclass/S1IF_updated.xlsx"
program_studi_id = 1

# Call the function
process_openedclass_dosen(file_path, program_studi_id)