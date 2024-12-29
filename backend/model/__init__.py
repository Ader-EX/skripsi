from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .dosen_model import Dosen
from .user_model import User
from .admin_model import Admin
from .mahasiswa_model import Mahasiswa
from .listkelas_model import ListKelas
from .mahasiswatimetable_model import MahasiswaTimeTable
from .timeslot_model import TimeSlot
from .matakuliah_model import MataKuliah
from .pengajaran_model import Pengajaran
from .preference_model import Preference
from .ruangan_model import Ruangan
