from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey
from .dosenopened_model import openedclass_dosen

class OpenedClass(Base):
    __tablename__ = "opened_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # mata_kuliah_program_studi_id: Mapped[int] = mapped_column(ForeignKey("mata_kuliah_program_studi.id"), nullable=False)
    mata_kuliah_kodemk: Mapped[str] = mapped_column(ForeignKey("mata_kuliah.kodemk"), nullable=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., "A", "B", "C", etc.
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False)  # Capacity of the class

    # Relationships
    dosens: Mapped[list["Dosen"]] = relationship("Dosen", secondary=openedclass_dosen, back_populates="opened_classes")
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="opened_classes")
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="opened_class")  # Add this line

