from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Date

from .dosenopened_model import openedclass_dosen



class Dosen(Base):
    __tablename__ = "dosen"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    pegawai_id : Mapped[int] =  mapped_column(Integer, nullable=True)
    nidn: Mapped[str] = mapped_column(String(20), nullable=True)
    nip: Mapped[str] = mapped_column(String(50), nullable=True)
    nomor_ktp: Mapped[str] = mapped_column(String(20), nullable=True)
    
    tanggal_lahir: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    progdi_id : Mapped[int] = mapped_column(Integer, nullable=True)
    ijin_mengajar: Mapped[bool] = mapped_column(Boolean, default=True)
    jabatan: Mapped[str] = mapped_column(String(100), nullable=True)
    title_depan: Mapped[str] = mapped_column(String(20), nullable=True)
    title_belakang: Mapped[str] = mapped_column(String(50), nullable=True)
    jabatan_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_sekdos: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dosen_kb: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"),nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="dosen")
    opened_classes: Mapped[list["OpenedClass"]] = relationship("OpenedClass", secondary=openedclass_dosen, back_populates="dosens")
    preferences : Mapped[list["Preference"]] = relationship("Preference",back_populates="dosen")

    def __repr__(self):
        return f"<Dosen({self.nama}, {self.nidn})>"