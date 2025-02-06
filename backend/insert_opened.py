import pandas as pd
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.dosen_model import Dosen
from model.dosenopened_model import openedclass_dosen

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("openedclass_duplicates.log"),
        logging.StreamHandler()
    ]
)

def determine_capacity(nama_mk: str) -> int:
    """ Determines the class capacity based on the course type. """
    return 40 if "praktikum" in nama_mk.lower() else 45

def insert_opened_classes(file_path):
    logging.info("🚀 Script started: insert_opened_classes()")

    session = SessionLocal()
    duplicates = []

    try:
        df = pd.read_excel(file_path)
        logging.info(f"📂 Read Excel file: {file_path}, Total Rows: {len(df)}")

        for index, row in df.iterrows():
            try:
                # Extract required values
                kodemk = row["f_kodemk"].strip()
                kelas = row["f_kelas"].strip().upper()
                dosen_id = row["dosen_id"]

                logging.debug(f"🔍 Processing: kodemk={kodemk}, kelas={kelas}, dosen_id={dosen_id}")

                # Find MataKuliah
                mata_kuliah = session.query(MataKuliah).filter_by(kodemk=kodemk).first()
                if not mata_kuliah:
                    logging.warning(f"⚠️ MataKuliah not found: kodemk={kodemk}")
                    continue

                # Determine class capacity
                kapasitas = determine_capacity(row["f_namamk"])

                # Check if OpenedClass already exists
                opened_class = session.query(OpenedClass).filter_by(
                    mata_kuliah_kodemk=mata_kuliah.kodemk,
                    kelas=kelas
                ).first()

                if not opened_class:
                    # Create new OpenedClass
                    opened_class = OpenedClass(
                        mata_kuliah_kodemk=mata_kuliah.kodemk,
                        kelas=kelas,
                        kapasitas=kapasitas
                    )
                    session.add(opened_class)
                    session.commit()  # Commit to get the ID
                    logging.info(f"✅ Inserted OpenedClass: kodemk={kodemk}, kelas={kelas}, kapasitas={kapasitas}")
                else:
                    logging.info(f"🟡 OpenedClass already exists: kodemk={kodemk}, kelas={kelas}")

                # Check if Dosen exists
                dosen = session.query(Dosen).filter_by(id=dosen_id).first()
                if not dosen:
                    logging.warning(f"⚠️ Dosen ID {dosen_id} not found. Skipping.")
                    continue

                # Check if association exists
                association_exists = session.execute(
                    openedclass_dosen.select().where(
                        (openedclass_dosen.c.opened_class_id == opened_class.id) &
                        (openedclass_dosen.c.dosen_id == dosen.id)
                    )
                ).first()

                if not association_exists:
                    # Insert into association table
                    session.execute(
                        openedclass_dosen.insert().values(
                            opened_class_id=opened_class.id,
                            dosen_id=dosen.id
                        )
                    )
                    logging.info(f"✅ Associated Dosen {dosen_id} with class {kelas} of {kodemk}")
                else:
                    logging.info(f"🟡 Dosen {dosen_id} already associated with class {kelas} of {kodemk}")

                # Commit changes
                session.commit()

            except Exception as row_error:
                logging.error(f"❌ Error processing row {index + 1}: {row_error}")
                session.rollback()

        logging.info(f"🎯 Finished processing. Skipped {len(duplicates)} duplicates.")

    except Exception as e:
        logging.error(f"❌ Fatal Error: {e}")
        session.rollback()
    finally:
        session.close()

# Run the function
insert_opened_classes("datas/openedclass/S1IF_updated.xlsx")
