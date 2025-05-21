from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, Optional, List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, validator

from database import get_db
from model.dosen_model import Dosen
from model.matakuliah_model import MataKuliah
from model.openedclass_model import OpenedClass
from model.ruangan_model import Ruangan
from model.user_model import User
from model.openedclass_model import OpenedClass



import model.timetable_model as timetable_model
from model.academicperiod_model import AcademicPeriods
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session



router = APIRouter()
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO
import pandas as pd

from database import get_db
import model.timetable_model as timetable_model
from model.academicperiod_model import AcademicPeriods  # <— import the right model

router = APIRouter()

@router.get("/export-timetable", status_code=status.HTTP_200_OK)
async def export_timetable(
    program_studi_id: Optional[int] = Query(None, description="Filter by Program Studi ID"),
    db: Session = Depends(get_db)
):
    # 1) load the active academic period from the AcademicPeriods table
    active = (
        db.query(AcademicPeriods)
          .filter(AcademicPeriods.is_active == True)
          .first()
    )
    if not active:
        raise HTTPException(404, "No active academic period found")



    timetables = (
        db.query(timetable_model.TimeTable)
        .filter(timetable_model.TimeTable.academic_period_id == active.id)
        .options(
          joinedload(timetable_model.TimeTable.opened_class)
              .joinedload(OpenedClass.mata_kuliah),
          joinedload(timetable_model.TimeTable.opened_class)
              .joinedload(OpenedClass.dosens),
          joinedload(timetable_model.TimeTable.ruangan),
          joinedload(timetable_model.TimeTable.academic_period)
      )
      .all()
)
        # 3) optional program studi filter
    if program_studi_id is not None:
        timetables = [
            t for t in timetables
            if t.opened_class.mata_kuliah.program_studi_id == program_studi_id
        ]


    rows = []
    for t in timetables:
        if program_studi_id and t.opened_class.mata_kuliah.program_studi_id != program_studi_id:
            continue

        for ts in t.timeslots:
            for i, dosen in enumerate(t.opened_class.dosens, start=1):
                rows.append({
                    "f_kodemk": t.opened_class.mata_kuliah_kodemk,
                    "f_semester": t.opened_class.mata_kuliah.smt,
                    "f_thakad": t.academic_period.tahun_ajaran,
                    "f_namamk": t.opened_class.mata_kuliah.namamk,
                    "f_sks_kurikulum": t.opened_class.mata_kuliah.sks,
                    "f_kelas": t.kelas,
                    "namakelompok": ts.day.value,
                    "f_jammulai": ts.start_time,
                    "f_jamselesai": ts.end_time,
                    "f_koderuang": t.ruangan.kode_ruangan,
                    "f_jumlahpeserta": t.kapasitas,
                    "f_urutandosen": i,
                    "f_namapegawai": dosen.nama,
                    "f_title_depan": dosen.title_depan,
                    "f_title_belakang": dosen.title_belakang,
                })



    # 4) pivot & build DataFrame
    df = pd.DataFrame(rows)

   
    df.rename(columns={
        "day": "Days",
        "start_time": "Start",
        "end_time": "End",
    }, inplace=True)

    # 5) write to Excel and stream
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Timetable")
    output.seek(0)

    headers = {
        "Content-Disposition": f"attachment; filename=timetable_{active.id}.xlsx"
    }
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
    
_PALETTE = [
    "#FFC7CE","#C6EFCE","#FFEB9C","#9CC2E5",
    "#D9E1F2","#F2DCDB","#FCE4D6","#E2EFDA",
    "#F4CCCC","#D5A6BD","#EAD1DC","#FFF2CC"
]

# Indonesian weekday names
_DAY_MAP = {
    "monday":   "Senin",
    "tuesday":  "Selasa",
    "wednesday":"Rabu",
    "thursday": "Kamis",
    "friday":   "Jumat"
}

def _assign_colors(kodemk_list):
    mapping = {}
    for i, km in enumerate(sorted(set(kodemk_list))):
        mapping[km] = _PALETTE[i % len(_PALETTE)]
    return mapping

def generate_time_room_matrix(timetables):
    """
    Build a single-sheet Excel where:
      - X axis = times (one column per unique start_time)
      - Y axis = rooms
      - Days (Senin–Jumat) merged automatically via pandas MultiIndex
      - Each cell colored uniquely per kodemk and contains the label.
    """
    from io import BytesIO
    from datetime import datetime
    import pandas as pd

    # 1) Build a “long” dataframe
    rows = []
    for t in timetables:
        km     = t.opened_class.mata_kuliah_kodemk
        smt    = t.opened_class.mata_kuliah.smt
        kelas  = t.kelas
        prodi  = t.opened_class.mata_kuliah.program_studi.name
        label  = f"{t.opened_class.mata_kuliah.namamk} ({smt}{kelas}-{prodi})"
        for ts in t.timeslots:
            day_py = ts.day.value.capitalize()            # “Monday”, etc.
            hari   = _DAY_MAP.get(day_py, day_py)         # map to “Senin”,…
            jam    = ts.start_time.strftime("%H:%M")
            rows.append({
                "Ruangan": t.ruangan.kode_ruangan,
                "Hari":    hari,
                "Jam":     jam,
                "Kodemk":  km,
                "Label":   label
            })

    df_long = pd.DataFrame(rows)
    if df_long.empty:
        raise ValueError("No timetable data to export")

    # 2) Pivot into a grid: index=Ruangan, columns=(Hari, Jam)
    df_wide = (
        df_long
        .pivot_table(
            index="Ruangan",
            columns=["Hari","Jam"],
            values="Label",
            aggfunc=lambda x: "\n".join(x),
            fill_value=""
        )
    )

    # 3) Reindex columns to ensure Senin–Jumat order and times sorted
    ordered_days = ["Senin","Selasa","Rabu","Kamis","Jumat"]
    ordered_jams = sorted(
        df_wide.columns.levels[1],
        key=lambda s: datetime.strptime(s, "%H:%M")
    )
    new_cols = [
        (day, jam)
        for day in ordered_days
        for jam in ordered_jams
        if (day, jam) in df_wide.columns
    ]
    df_wide = df_wide.reindex(columns=pd.MultiIndex.from_tuples(new_cols))

    # 4) Write to Excel and color
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_wide.to_excel(writer, sheet_name="Jadwal")
        wb = writer.book
        ws = writer.sheets["Jadwal"]

        # Build color map by kodemk
        palette = _PALETTE
        unique_km = df_long["Kodemk"].unique()
        color_map = {km: palette[i % len(palette)]
                     for i, km in enumerate(sorted(unique_km))}

        # Formats
        wrap_fmt = {"text_wrap": True, "valign": "top"}

        # Offsets: pandas writes index name in A1, then two header rows, so data starts at row 3
        row_offset = 2
        col_offset = 1

        # Loop cells and apply colors
        for r_idx, room in enumerate(df_wide.index, start=row_offset):
            for c_idx, (hari, jam) in enumerate(df_wide.columns, start=col_offset):
                val = df_wide.iat[r_idx-row_offset, c_idx-col_offset]
                if val:
                    # pick first kodemk for color
                    mask = (
                        (df_long["Ruangan"] == room) &
                        (df_long["Hari"] == hari) &
                        (df_long["Jam"]  == jam)
                    )
                    km = df_long.loc[mask, "Kodemk"].iat[0]
                    fmt = wb.add_format({**wrap_fmt, "fg_color": color_map[km]})
                    ws.write(r_idx+1, c_idx, val, fmt)  # +1 for pandas index-name row
                else:
                    ws.write(r_idx+1, c_idx, "", wb.add_format(wrap_fmt))

        # Column widths & freeze pane
        ws.set_column(0, 0, 12)
        for c in range(1, df_wide.shape[1] + 1):
            ws.set_column(c, c, 20)
        ws.freeze_panes(row_offset+1, col_offset)

    output.seek(0)
    return output


@router.get("/export-timetable-matrix", status_code=status.HTTP_200_OK)
async def export_timetable_matrix(
    program_studi_id: Optional[int] = Query(None, description="Filter by Program Studi ID"),
    db: Session = Depends(get_db)
):
    # load active period
    active = db.query(AcademicPeriods).filter_by(is_active=True).first()
    if not active:
        raise HTTPException(404, "No active academic period found")

    # fetch timetables
    tms = (
        db.query(timetable_model.TimeTable)
          .filter_by(academic_period_id=active.id)
          .options(
             joinedload(timetable_model.TimeTable.opened_class)
               .joinedload(OpenedClass.mata_kuliah)
               .joinedload(MataKuliah.program_studi),
             joinedload(timetable_model.TimeTable.ruangan),
             joinedload(timetable_model.TimeTable.academic_period)
          )
          .all()
    )

    # apply program studi filter
    if program_studi_id is not None:
        tms = [t for t in tms
               if t.opened_class.mata_kuliah.program_studi_id == program_studi_id]

    # build & return Excel
    bio = generate_time_room_matrix(tms)
    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
              f"attachment; filename=timetable_matrix_{active.id}.xlsx"
        }
    )