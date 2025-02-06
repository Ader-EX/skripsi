from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .dosen_model import Dosen
from .user_model import User
from .mahasiswa_model import Mahasiswa

from .mahasiswatimetable_model import MahasiswaTimeTable

from .timeslot_model import TimeSlot
from .matakuliah_model import MataKuliah

from .preference_model import Preference
from .ruangan_model import Ruangan
from .openedclass_model import OpenedClass
from .programstudi_model import ProgramStudi
# from .matakuliah_programstudi import MataKuliahProgramStudi
from .academicperiod_model import AcademicPeriods