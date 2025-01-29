from sqlalchemy import Table, Column, ForeignKey
from database import Base

openedclass_dosen = Table(
    "openedclass_dosen",
    Base.metadata,
    Column("opened_class_id", ForeignKey("opened_class.id"), primary_key=True),
    Column("dosen_id", ForeignKey("dosen.id"), primary_key=True),
)