from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    # Basic Info
    tahun_masuk = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    sks_diambil = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    mahasiswa_timetables = relationship("MahasiswaTimeTable", back_populates="mahasiswa")
    
    # Profile Info
    nama = Column(String(255), nullable=False)
    tgl_lahir = Column(Date, nullable=False)
    kota_lahir = Column(String(255), nullable=False)
    jenis_kelamin = Column(String(10), nullable=False)
    kewarganegaraan = Column(String(50), nullable=False)
    alamat = Column(String(255), nullable=False)
    kode_pos = Column(Integer, nullable=True)
    hp = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    nama_ayah = Column(String(255), nullable=True)
    nama_ibu = Column(String(255), nullable=True)
    pekerjaan_ayah = Column(String(255), nullable=True)
    pekerjaan_ibu = Column(String(255), nullable=True)
    status_kawin = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="mahasiswa")
    program_studi = relationship("ProgramStudi", back_populates="mahasiswa")