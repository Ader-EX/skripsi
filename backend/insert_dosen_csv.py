# import pandas as pd
# import random
# from datetime import datetime
# from sqlalchemy.orm import Session
# from database import SessionLocal
# from model.dosen_model import Dosen
# from model.user_model import User

# # Password hashing context


# # Path to the CSV file
# csv_file_path = "datas/dosen205.csv"

# def generate_nip():
#     """Generate a random Indonesian-style NIP (18 digits)."""
#     return "".join([str(random.randint(0, 9)) for _ in range(18)])

# def parse_date(date_value):
#     """Parses date input, handling both strings and datetime objects. Defaults to 5/29/2005 if invalid."""
#     default_date = datetime.strptime("5/29/2005", "%m/%d/%Y")  # Default date object

#     if isinstance(date_value, datetime):
#         return date_value  # ✅ Already a datetime object, return as is

#     if not date_value or str(date_value).strip().lower() in ["nan", "none", ""]:
#         print(f"⚠️ Missing date. Using default: {default_date.strftime('%Y-%m-%d')}")
#         return default_date

#     # Handle different date formats
#     possible_formats = ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]
    
#     for fmt in possible_formats:
#         try:
#             return datetime.strptime(str(date_value), fmt)
#         except ValueError:
#             continue
    
#     print(f"❌ Failed to parse date: {date_value}. Using default: {default_date.strftime('%Y-%m-%d')}")
#     return default_date

# def safe_int(value):
#     """Convert a value to int if it's valid, otherwise return None."""
#     return int(value) if pd.notna(value) and str(value).isdigit() else None

# def safe_str(value):
#     """Convert a value to a string if it's valid, otherwise return None."""
#     return str(value).strip() if pd.notna(value) and value not in ["nan", "NaN", "None", ""] else None

# def safe_bool(value):
#     """Convert a T/F string to boolean."""
#     return value.strip().upper() == "T" if pd.notna(value) else None

# def load_csv_to_database(file_path):
#     duplicates = []
#     session = SessionLocal()

#     try:
#         df = pd.read_csv(file_path, dtype=str)  
#         df = df.where(pd.notna(df), None)  # Convert NaN to None globally

#         # Only process rows where ID >= 205
#         df = df[df["id"].astype(int) >= 205]

#         for _, row in df.iterrows():
#             try:
#                 pegawai_id = safe_int(row.get("pegawai_id"))
#                 nama = safe_str(row.get("nama"))
#                 nip = safe_str(row.get("nip")) or generate_nip()  # Generate NIP if missing
#                 nidn = safe_str(row.get("nidn"))
#                 email = safe_str(row.get("email"))
#                 tanggal_lahir = parse_date(row.get("tanggal_lahir"))

#                 if not pegawai_id or not nama:
#                     print(f"⚠️ Skipping row: Missing pegawai_id or nama -> {row.to_dict()}")
#                     continue

#                 print(f"📌 Processing {pegawai_id} - {nama}")

#                 # Check for existing user
#                 existing_user = session.query(User).filter_by(nim_nip=nip).first()
#                 if existing_user:
#                     print(f"🔴 User {nip} already exists. Skipping.")
#                     duplicates.append(row.to_dict())
#                     continue

#                 # Insert new user
#                 new_user = User(
#                     nim_nip=nip,
#                     password=hash_password("dosen"),
#                     role="dosen"
#                 )
#                 session.add(new_user)
#                 session.commit()
#                 session.refresh(new_user)  # Ensure user ID is available

#                 # Insert new dosen
#                 new_dosen = Dosen(
#                     pegawai_id=pegawai_id,
#                     nama=nama,
#                     nidn=nidn,
#                     nomor_ktp=safe_str(row.get("nomor_ktp")),
#                     email=email,
#                     tanggal_lahir=tanggal_lahir,
#                     progdi_id=safe_int(row.get("progdi_id")),
#                     ijin_mengajar=safe_bool(row.get("ijin_mengajar")),
#                     jabatan=safe_str(row.get("jabatan")),
#                     title_depan=safe_str(row.get("title_depan")),
#                     title_belakang=safe_str(row.get("title_belakang")),
#                     jabatan_id=safe_int(row.get("jabatan_id")),
#                     is_sekdos=safe_bool(row.get("is_sekdos")),
#                     user_id=new_user.id  # Link new user ID
#                 )

#                 print(f"✅ Inserting Dosen: {new_dosen}")
#                 session.add(new_dosen)

#             except Exception as row_error:
#                 print(f"❌ Error processing row {row.to_dict()}: {row_error}")

#         session.commit()
#         print("✅ All valid rows inserted.")

#     except Exception as e:
#         print(f"❌ Fatal error: {e}")
#         session.rollback()
#     finally:
#         session.close()


# # Run the loader
# load_csv_to_database(csv_file_path)
