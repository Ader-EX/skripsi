from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey

class MataKuliah(Base):
    __tablename__ = "mata_kuliah"
    
    kodemk: Mapped[str] = mapped_column(String(20), primary_key=True)
    namamk: Mapped[str] = mapped_column(String(255), nullable=False)
    sks: Mapped[int] = mapped_column(Integer, nullable=False)
    smt: Mapped[int] = mapped_column(Integer, nullable=False)
    kurikulum: Mapped[str] = mapped_column(String(20), nullable=False)
    status_mk: Mapped[str] = mapped_column(String(1), nullable=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)

    tipe_mk: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    pengajaran: Mapped[list["Pengajaran"]] = relationship("Pengajaran", back_populates="mata_kuliah")

    def __repr__(self):
        return f"<MataKuliah({self.id}, {self.nama}, {self.sks} SKS)>"