import pandas as pd
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.dosen_model import Dosen
from model.dosenopened_model import openedclass_dosen
from sqlalchemy import func
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("openedclass_duplicates.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def determine_capacity(nama_mk: str) -> int:
    """ Determines the class capacity based on the course type. """
    return 35 if "praktikum" in nama_mk.lower() else 35

def insert_opened_classes(file_path):
    logging.info("🚀 Script started: insert_opened_classes()")

    session = SessionLocal()
    duplicates = []

    try:
        df = pd.read_excel(file_path)
        logging.info(f"📂 Read Excel file: {file_path}, Total Rows: {len(df)}")

        # Group by kodemk and kelas to determine dosen besar
        dosen_counts = df.groupby(['f_kodemk', 'dosen_id']).size().reset_index(name='count')
        dosen_counts['is_dosen_besar'] = dosen_counts.groupby(['f_kodemk'])['count'].transform(lambda x: x == x.max())
        
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
                dosen = session.query(Dosen).filter_by(pegawai_id=dosen_id).first()
                if not dosen:
                    logging.warning(f"⚠️ Dosen ID {dosen_id} not found. Skipping.")
                    continue

                # Determine if dosen is dosen besar for this mata kuliah
                is_dosen_besar = dosen_counts.loc[
                    (dosen_counts['f_kodemk'] == kodemk) &
                    (dosen_counts['dosen_id'] == dosen_id), 
                    'is_dosen_besar'
                ].iloc[0]

               # Determine if dosen is teaching the class alone
                dosen_count_for_class = session.query(func.count(openedclass_dosen.c.dosen_id)).filter_by(opened_class_id=opened_class.id).scalar()

                # Determine if dosen's preference should be used
                use_preference = dosen_count_for_class == 1 or (not is_dosen_besar and dosen_count_for_class > 1)

                # Check if association exists
                association_exists = session.execute(
                    openedclass_dosen.select().where(
                        (openedclass_dosen.c.opened_class_id == opened_class.id) &
                        (openedclass_dosen.c.dosen_id == dosen.pegawai_id)
                    )
                ).first()

                if not association_exists:
                    # Insert into association table
                    session.execute(
                        openedclass_dosen.insert().values(
                            opened_class_id=opened_class.id,
                            dosen_id=dosen.pegawai_id,
                            used_preference=use_preference
                        )
                    )
                    logging.info(f"✅ Associated Dosen {dosen_id} with class {kelas} of {kodemk}, used_preference={use_preference}")
                else:
                    # Update used_preference
                    session.execute(
                        openedclass_dosen.update().where(
                            (openedclass_dosen.c.opened_class_id == opened_class.id) &
                            (openedclass_dosen.c.dosen_id == dosen.pegawai_id)
                        ).values(used_preference=use_preference)
                    )
                    logging.info(f"🟡 Updated used_preference to {use_preference} for Dosen {dosen_id} with class {kelas} of {kodemk}")
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
insert_opened_classes("datas/openedclass/S1SI_updated_updated.xlsx")

# Recheck and update used_preference for dosens teaching a class alone
def update_solo_dosen_preference():
    logging.info("🔍 Rechecking and updating used_preference for solo dosens")

    session = SessionLocal()

    try:
        # Get all opened_classes
        opened_classes = session.query(OpenedClass).all()

        for opened_class in opened_classes:
            # Count the number of dosens for each opened_class
            dosen_count = session.query(func.count(openedclass_dosen.c.dosen_id)).filter_by(opened_class_id=opened_class.id).scalar()

            if dosen_count == 1:
                # If only one dosen teaches the class, set their used_preference to 1
                solo_dosen = session.query(openedclass_dosen).filter_by(opened_class_id=opened_class.id).first()
                
                if solo_dosen.used_preference == 0:
                    session.execute(
                        openedclass_dosen.update().where(
                            (openedclass_dosen.c.opened_class_id == opened_class.id) &
                            (openedclass_dosen.c.dosen_id == solo_dosen.dosen_id)
                        ).values(used_preference=1)
                    )
                    logging.info(f"✅ Updated used_preference to 1 for solo Dosen {solo_dosen.dosen_id} in OpenedClass {opened_class.id}")

        session.commit()
        logging.info("🎉 Finished updating used_preference for solo dosens")

    except Exception as e:
        logging.error(f"❌ Error updating used_preference for solo dosens: {e}")
        session.rollback()

    finally:
        session.close()

# Run the solo dosen preference update
update_solo_dosen_preference()
