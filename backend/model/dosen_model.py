from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Date

class Dosen(Base):
    __tablename__ = "dosen"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nidn: Mapped[str] = mapped_column(String(20), nullable=True)
    nip: Mapped[str] = mapped_column(String(50), nullable=True)
    nomor_ktp: Mapped[str] = mapped_column(String(20), nullable=True)
    nama: Mapped[str] = mapped_column(String(255), nullable=False)
    tanggal_lahir: Mapped[Date] = mapped_column(Date, nullable=True)
    progdi_id: Mapped[int] = mapped_column(ForeignKey("progdi.id"), nullable=False)
    ijin_mengajar: Mapped[bool] = mapped_column(Boolean, default=True)
    jabatan: Mapped[str] = mapped_column(String(100), nullable=True)
    title_depan: Mapped[str] = mapped_column(String(20), nullable=True)
    title_belakang: Mapped[str] = mapped_column(String(50), nullable=True)
    jabatan_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_sekdos: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dosen_kb: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dosen")
    pengajaran: Mapped[list["Pengajaran"]] = relationship("Pengajaran", back_populates="dosen")
    progdi: Mapped["Progdi"] = relationship("Progdi", back_populates="dosen")

    def __repr__(self):
        return f"<Dosen({self.nama}, {self.nidn})>"