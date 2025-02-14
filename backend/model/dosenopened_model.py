from sqlalchemy import Boolean, Table, Column, ForeignKey
from database import Base

openedclass_dosen = Table(
    "openedclass_dosen",
    Base.metadata,
    Column("opened_class_id", ForeignKey("opened_class.id"), primary_key=True),
    Column("dosen_id", ForeignKey("dosen.pegawai_id"), primary_key=True),
    Column("used_preference",  Boolean, default=False)
)