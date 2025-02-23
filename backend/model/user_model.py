from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nim_nip : Mapped[str] =  mapped_column(String(50), nullable=False,unique= True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # One-to-One Relationships
    mahasiswa: Mapped["Mahasiswa"] = relationship("Mahasiswa", back_populates="user", uselist=False)
    dosen: Mapped["Dosen"] = relationship("Dosen", back_populates="user", uselist=False)

