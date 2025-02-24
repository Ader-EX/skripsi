import React from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  BookOpen,
  Building2,
  Users,
  GraduationCap,
  ClipboardCheck,
  Layers,
  Table,
  AlignLeft,
  Calendar1,
} from "lucide-react";

import MahasiswaManagement from "@/components/tables/mahasiswa/MahasiswaManagement";
import AcademicPeriodManagement from "@/components/tables/academic-period/AcademicPeriodManagement";
import RuanganManagement from "@/components/pages/RuanganManagement";
import MataKuliahManagement from "@/components/pages/MataKuliahManagement";
import OpenedClassManagement from "@/components/tables/opened-class/OpenedClassManagement";
import MahasiswaTimeTableManagement from "@/components/tables/mahasiswa-timetable-management/MahasiswaTimeTableManagement";
import TimeTableManagement from "@/components/tables/time-table/TimeTableManagement";
import DosenManagement from "@/components/tables/dosen/DosenManagement";
import DosenTimeTableManagement from "@/components/tables/dosen-timetable-management/DosenTimetableManagement";

const AdminManagement = () => {
  const tabs = [
    { value: "timetable", icon: AlignLeft, label: "Jadwal Saat ini" },
    { value: "opened-class", icon: ClipboardCheck, label: "Kelas Dibuka" },
    { value: "matakuliah", icon: BookOpen, label: "Mata Kuliah" },
    { value: "mahasiswa-timetable", icon: Layers, label: "Jadwal Mhs" },
    { value: "dosen-timetable", icon: Layers, label: "Jadwal Dosen" },
    { value: "ruangan", icon: Building2, label: "Ruangan" },
    { value: "dosen", icon: Users, label: "Dosen" },
    { value: "mahasiswa", icon: GraduationCap, label: "Mahasiswa" },
    // { value: "program-studi", icon: Table, label: "Program Studi" },
    { value: "academic-periods", icon: Calendar1, label: " Klr. Akademik" },
  ];

  return (
    <div className="container mx-auto p-4 md:p-6">
      <h1 className="text-xl md:text-2xl font-bold mb-4 md:mb-6">
        Sistem Manajemen Akademik
      </h1>

      <Tabs defaultValue="timetable" className="space-y-4 md:space-y-6">
        <div className=" mb-[12rem] md:mb-[6rem] sm:mb-[12rem]  ">
          <TabsList className="text-primary p-1 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {tabs.map(({ value, icon: Icon, label }) => (
              <TabsTrigger
                key={value}
                value={value}
                className="flex items-center gap-1 md:gap-2 px-3 py-2 text-sm md:text-base whitespace-nowrap"
              >
                <Icon className="h-4 w-4 md:h-5 md:w-5" />
                <span>{label}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </div>

        {/* Existing Tabs */}
        <TabsContent
          value="matakuliah"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <MataKuliahManagement />
        </TabsContent>

        <TabsContent value="ruangan" className="border-none p-0 mt-4 md:mt-6">
          <RuanganManagement />
        </TabsContent>

        <TabsContent
          value="academic-periods"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <AcademicPeriodManagement />
        </TabsContent>

        <TabsContent value="mahasiswa" className="border-none p-0 mt-4 md:mt-6">
          <MahasiswaManagement />
        </TabsContent>

        <TabsContent
          value="opened-class"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <OpenedClassManagement />
        </TabsContent>

        <TabsContent
          value="mahasiswa-timetable"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <MahasiswaTimeTableManagement />
        </TabsContent>

        <TabsContent
          value="dosen-timetable"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <DosenTimeTableManagement />
        </TabsContent>

        {/* <TabsContent
          value="program-studi"
          className="border-none p-0 mt-4 md:mt-6"
        >
          <ProgramStudiManagement />
        </TabsContent> */}

        <TabsContent value="timetable" className="border-none p-0 mt-4 md:mt-6">
          <TimeTableManagement />
        </TabsContent>

        <TabsContent value="dosen" className="border-none p-0 mt-4 md:mt-6">
          <DosenManagement />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminManagement;
