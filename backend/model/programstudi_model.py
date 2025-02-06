from database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, ForeignKey



class ProgramStudi(Base):
    __tablename__ = "program_studi"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # Relationships
    mata_kuliah: Mapped[list["MataKuliah"]] = relationship("MataKuliah", back_populates="program_studi")
    mahasiswa: Mapped[list["Mahasiswa"]] = relationship("Mahasiswa", back_populates="program_studi")

    def __repr__(self):
        return f"<ProgramStudi(id={self.id}, name={self.name})>"
