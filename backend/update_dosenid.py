import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal
from model.dosen_model import Dosen

# Path to the Excel file
xlsx_file_path = "datas/openedclass/S1SI_updated.xlsx"

def update_dosen_id(file_path):
    """Update the dosen_id column in the Excel file based on nama matching in the database."""
    
    # Open a database session
    session = SessionLocal()
    
    try:
        # Load the Excel file into a DataFrame
        df = pd.read_excel(file_path, dtype=str)

        # Fetch all dosens from the database
        dosen_mapping = {d.nama.strip().lower(): d.pegawai_id for d in session.query(Dosen).all()}

        # Update dosen_id based on f_namapegawai
        updated_count = 0

        for index, row in df.iterrows():
            f_namapegawai = str(row.get("f_namapegawai")).strip().lower()

            if f_namapegawai in dosen_mapping:
                correct_dosen_id = dosen_mapping[f_namapegawai]

                if str(row.get("dosen_id")) != str(correct_dosen_id):  # Only update if different
                    df.at[index, "dosen_id"] = correct_dosen_id
                    updated_count += 1
            else:
                print(f"⚠️ No matching dosen found for: {row.get('f_namapegawai')}")

        # Save the updated DataFrame back to Excel
        updated_file_path = file_path.replace(".xlsx", "_updated.xlsx")
        df.to_excel(updated_file_path, index=False)
        
        print(f"✅ Successfully updated {updated_count} records.")
        print(f"📁 Updated file saved as: {updated_file_path}")

    except Exception as e:
        print(f"❌ Error updating dosen_id: {e}")
    
    finally:
        session.close()

# Run the function
update_dosen_id(xlsx_file_path)
