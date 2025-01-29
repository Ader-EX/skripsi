from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey
from .dosenopened_model import openedclass_dosen

class OpenedClass(Base):
    __tablename__ = "opened_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mata_kuliah_program_studi_id: Mapped[int] = mapped_column(ForeignKey("mata_kuliah_program_studi.id"), nullable=False)
    kelas: Mapped[str] = mapped_column(String(10), nullable=False)  # E.g., "A", "B", "C", etc.
    kapasitas: Mapped[int] = mapped_column(Integer, nullable=False)  # Capacity of the class

    # Relationships
    dosens: Mapped[list["Dosen"]] = relationship("Dosen", secondary=openedclass_dosen, back_populates="opened_classes")
    mata_kuliah_program_studi: Mapped["MataKuliahProgramStudi"] = relationship(
        "MataKuliahProgramStudi",
        back_populates="opened_classes",
        overlaps="mata_kuliah, opened_classes"  # Resolve conflict with mata_kuliah relationship
    )
    timetables: Mapped[list["TimeTable"]] = relationship("TimeTable", back_populates="opened_class")  # Add this line

    def __repr__(self):
        return f"<OpenedClass(id={self.id}, mata_kuliah_program_studi_id={self.mata_kuliah_program_studi_id}, kelas={self.kelas})>"