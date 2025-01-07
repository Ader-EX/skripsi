from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean, Table, Column


class MataKuliahProgramStudi(Base):
    __tablename__ = "mata_kuliah_program_studi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mata_kuliah_id: Mapped[str] = mapped_column(ForeignKey("mata_kuliah.kodemk"), nullable=False)
    program_studi_id: Mapped[int] = mapped_column(ForeignKey("program_studi.id"), nullable=False)
    tahun_ajaran: Mapped[str] = mapped_column(String(10), nullable=True)  # Example: "2023/2024"
    semester: Mapped[int] = mapped_column(Integer, nullable=True)  # Example: 1 or 2

    # Relationships
    mata_kuliah: Mapped["MataKuliah"] = relationship("MataKuliah", back_populates="program_studi_associations")
    program_studi: Mapped["ProgramStudi"] = relationship("ProgramStudi", back_populates="mata_kuliah_associations")
    opened_classes: Mapped[list["OpenedClass"]] = relationship("OpenedClass", back_populates="mata_kuliah_program_studi")  # Add this relationship

    def __repr__(self):
        return f"<MataKuliahProgramStudi(mata_kuliah_id={self.mata_kuliah_id}, program_studi_id={self.program_studi_id}, tahun_ajaran={self.tahun_ajaran}, semester={self.semester})>"