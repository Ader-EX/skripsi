import TimeTableDashboardReadOnly from "@/components/global/TimeTableDashboardReadOnly";
import React from "react";

const MahasiswaTabelJadwal = () => {
  return (
    <div className="p-6 flex w-full flex-col gap-6">
      <h1 className="text-2xl font-bold ">Dashboard</h1>
      <h2 className="text-xl font-semibold ">Selamat Datang</h2>
      <TimeTableDashboardReadOnly />
    </div>
  );
};

export default MahasiswaTabelJadwal;
