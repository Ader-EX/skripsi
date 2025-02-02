import React from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";

const MahasiswaDashboard = () => {
  const courses = [
    {
      code: "INFAG89901",
      name: "Analisis Dan..",
      class: "A",
      sks: "3",
      schedule: "Selasa - 07:00-09:30 ( FIK-402 - [U..",
      lecturer: "1. Kharisma Wisti Gusti, S.T. M.T..",
    },
    {
      code: "INF9B86HNBM",
      name: "Algoritma Pe..",
      class: "A",
      sks: "2",
      schedule: "Selasa - 09:30-10:30 ( FIKLAB-301 -..",
      lecturer: "1. Ridwan Raafi'udin, M.Kom..",
    },
    {
      code: "INF2456SZZA",
      name: "Statistika P..",
      class: "C",
      sks: "1",
      schedule: "Selasa - 10:30-12:00 ( FIK-302 - [U..",
      lecturer: "1. Hamonangan Kinantan P., M.T..",
    },
    {
      code: "INFYU664014",
      name: "Proposal",
      class: "A",
      sks: "1",
      schedule: "Rabu - 07:00-09:30 ( FIK-202 - [UP..",
      lecturer: "1. Agung Mulyo Widodo, ST, M.Sc..",
    },
    {
      code: "INFAGBN7312",
      name: "Teori Bahasa D..",
      class: "D",
      sks: "2",
      schedule: "Kamis - 07:00-09:30 ( FIKLAB-301 -..",
      lecturer: "1. Dr. Tata Sutabri, S.Kom., M.MSI..",
    },
    {
      code: "INFAGBN7792",
      name: "Rancang Bangun..",
      class: "E",
      sks: "3",
      schedule: "Jumat - 07:00-09:30 ( FIKLAB-401 -..",
      lecturer: "1. Dr. Tata Sutabri, S.Kom., M.MSI..",
    },
  ];

  return (
    <div className="w-full flex flex-col gap-y-4  mx-auto p-4">
      <h1 className="text-primary font-bold text-2xl">Dashboard</h1>
      <Card className="bg-surface border-border">
        <CardHeader className="bg-primary text-primary-foreground ">
          <h2 className="text-lg font-semibold">
            Periode Pengisian KRS 2024/2025 Ganjil
          </h2>
          <p className="text-sm opacity-90">
            07 Agustus 2024 Pukul 15.00 WIB s/d 08 Aug 2024 Pukul 23.59 WIB
          </p>
        </CardHeader>
        <CardContent className="p-4">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-surface border-b border-border">
                  <th className="p-3 text-left text-text-primary font-semibold">
                    KodeMK
                  </th>
                  <th className="p-3 text-left text-text-primary font-semibold">
                    Mata Kuliah
                  </th>
                  <th className="p-3 text-left text-text-primary font-semibold">
                    Kelas
                  </th>
                  <th className="p-3 text-left text-text-primary font-semibold">
                    SKS
                  </th>
                  <th className="p-3 text-left text-text-primary font-semibold">
                    Jadwal Pertemuan
                  </th>
                  <th className="p-3 text-left text-text-primary font-semibold">
                    Dosen
                  </th>
                </tr>
              </thead>
              <tbody>
                {courses.map((course, index) => (
                  <tr
                    key={course.code}
                    className={`border-b border-border hover:bg-surface/80 transition-colors
                      ${index % 2 === 0 ? "bg-white" : "bg-surface"}`}
                  >
                    <td className="p-3 text-text-primary">{course.code}</td>
                    <td className="p-3 text-text-primary">{course.name}</td>
                    <td className="p-3 text-text-primary">{course.class}</td>
                    <td className="p-3 text-text-primary">{course.sks}</td>
                    <td className="p-3 text-text-primary">{course.schedule}</td>
                    <td className="p-3 text-text-primary">{course.lecturer}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 space-y-4">
            <div className="bg-info/10 p-4 rounded-lg">
              <h3 className="font-semibold text-text-primary mb-2">
                Informasi
              </h3>
              <p className="text-text-secondary text-sm">
                MASA PENGISIAN KRS ANDA TELAH DIBUKA, SILAKAN MELAKUKAN
                PENGISIAN KRS MULAI DARI 07/08/2024 15:00 HINGGA 08/08/2024
                23:59.
              </p>
              <p className="text-text-secondary text-sm mt-1">
                PASTIKAN ANDA SUDAH BERKONSULTASI DENGAN DOSEN PA SEBELUM
                MELAKUKAN PENGISIAN.
              </p>
            </div>

            <div className="space-y-2">
              <select className="w-full p-2 rounded-md border border-border bg-white text-text-primary">
                <option>Pilih Mata Kuliah Anda yang Ingin Diambil</option>
              </select>

              <button className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                + Tambah Mata Kuliah
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MahasiswaDashboard;
