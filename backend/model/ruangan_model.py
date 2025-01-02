from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer, Boolean

class Ruangan(Base):
    __tablename__ = "ruangan"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kode_ruangan: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nama_ruang: Mapped[str] = mapped_column(String(255), nullable=False)
    tipe_ruangan: Mapped[str] = mapped_column(String(1), nullable=False)
    jenis_ruang: Mapped[str] = mapped_column(String(1), nullable=False)
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False)
    status_aktif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    share_prodi: Mapped[bool] = mapped_column(Boolean, nullable=True)
    alamat: Mapped[str] = mapped_column(String(500), nullable=True)
    kode_mapping: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Relationships
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="ruangan")

    def __repr__(self):
        return f"<Ruangan({self.kode_ruangan}, {self.nama_ruang}, kapasitas={self.kapasitas})>"