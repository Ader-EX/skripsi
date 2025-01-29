from sqlalchemy import Table, ForeignKey, Column
from database import Base

# Association table for many-to-many relationship
pengajaran_dosen = Table(
    "pengajaran_dosen",
    Base.metadata,
    Column("pengajaran_id", ForeignKey("pengajaran.id"), primary_key=True),
    Column("dosen_id", ForeignKey("dosen.id"), primary_key=True),
)