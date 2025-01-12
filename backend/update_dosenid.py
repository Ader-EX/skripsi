import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import SessionLocal
from model.dosen_model import Dosen  # Ensure the path to your Dosen model is correct

# Path to the Excel file
xlsx_file_path = "datas/openedclass/S1SI.xlsx"

def load_xlsx_and_add_dosen_id(file_path):
    """
    Reads an Excel file, matches f_namapegawai with the nama column in the Dosen model,
    adds a dosen_id column, and saves the updated file.
    """
    # Initialize session
    session = SessionLocal()

    try:
        # Read the Excel file
        df = pd.read_excel(file_path)

        # Create a list to store unmatched names
        unmatched_names = []

        # Create a dosen_id list to hold IDs
        dosen_ids = []

        for _, row in df.iterrows():
            nama_pegawai = row["f_namapegawai"]

            # Query the Dosen table for the matching nama
            dosen = session.query(Dosen).filter(Dosen.nama == nama_pegawai).first()

            if dosen:
                dosen_ids.append(dosen.id)
            else:
                dosen_ids.append(None)
                unmatched_names.append(nama_pegawai)

        # Add the dosen_id column to the DataFrame
        df["dosen_id"] = dosen_ids

        # Save the updated DataFrame to a new Excel file
        output_file_path = file_path.replace(".xlsx", "_updated.xlsx")
        df.to_excel(output_file_path, index=False)

        print(f"Updated file saved to {output_file_path}")

        # Log unmatched names
        if unmatched_names:
            print("Unmatched names:")
            for name in unmatched_names:
                print(name)

    except Exception as e:
        print("Error occurred:", e)
    finally:
        session.close()

# Run the loader for the file
load_xlsx_and_add_dosen_id(xlsx_file_path)
