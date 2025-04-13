from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Mahasiswa(Base):
    __tablename__ = "mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
  
    nama = Column(String(255), nullable=False)
    tahun_masuk = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False, default=1)
    sks_diambil = Column(Integer, nullable=False, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    program_studi_id = Column(Integer, ForeignKey("program_studi.id"), nullable=False)
    mahasiswa_timetables = relationship("MahasiswaTimeTable", back_populates="mahasiswa")
    
    tgl_lahir = Column(Date, nullable=True)
    kota_lahir = Column(String(255), nullable=True)
    jenis_kelamin = Column(String(10), nullable=True, default="L")
    kewarganegaraan = Column(String(50), nullable=True, default="Indonesia")
    alamat = Column(String(255), nullable=True)
    kode_pos = Column(Integer, nullable=True)
    hp = Column(String(20), nullable=True)
  

    # Relationships
    user = relationship("User", back_populates="mahasiswa")
    program_studi = relationship("ProgramStudi", back_populates="mahasiswa")