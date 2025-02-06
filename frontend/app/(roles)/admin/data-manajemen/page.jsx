import React from "react";
import MataKuliahManagement from "@/components/pages/MataKuliahManagement";
import RuanganManagement from "@/components/pages/RuanganManagement";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  BookOpen,
  Building2,
  Users,
  GraduationCap,
  Calendar,
  Clock,
} from "lucide-react";
import AcademicPeriodManagement from "@/components/tables/academic-period/AcademicPeriodManagement";
import MahasiswaManagement from "@/components/tables/mahasiswa/MahasiswaManagement";

const AdminManagement = () => {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Sistem Manajemen Akademik</h1>

      <Tabs defaultValue="matakuliah" className="space-y-6">
        <TabsList className="text-primary p-1">
          <TabsTrigger value="matakuliah" className="flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            <span>Mata Kuliah</span>
          </TabsTrigger>

          <TabsTrigger value="ruangan" className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            <span>Ruangan</span>
          </TabsTrigger>

          <TabsTrigger value="dosen" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span>Dosen</span>
          </TabsTrigger>

          <TabsTrigger value="mahasiswa" className="flex items-center gap-2">
            <GraduationCap className="h-4 w-4" />
            <span>Mahasiswa</span>
          </TabsTrigger>

          <TabsTrigger
            value="academic-periods"
            className="flex items-center gap-2"
          >
            <Calendar className="h-4 w-4" />
            <span>Periode Akademik</span>
          </TabsTrigger>

          <TabsTrigger value="timeslot" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            <span>Slot Waktu</span>
          </TabsTrigger>
        </TabsList>

        {/* Mata Kuliah Management */}
        <TabsContent value="matakuliah" className="border-none p-0 mt-6">
          <MataKuliahManagement />
        </TabsContent>

        {/* Ruangan Management */}
        <TabsContent value="ruangan" className="border-none p-0 mt-6">
          <RuanganManagement />
        </TabsContent>

        {/* Academic Period Management ✅ */}
        <TabsContent value="academic-periods" className="border-none p-0 mt-6">
          <AcademicPeriodManagement /> {/* ✅ Now it renders here */}
        </TabsContent>
        <TabsContent value="mahasiswa" className="border-none p-0 mt-6">
          <MahasiswaManagement /> {/* ✅ Now it renders here */}
        </TabsContent>

        {/* Placeholder contents for other tabs */}
        {["dosen", "timeslot"].map((tab) => (
          <TabsContent key={tab} value={tab} className="border-none p-0 mt-6">
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
              <div className="text-center">
                <p className="text-lg font-medium text-gray-900 mb-2">
                  {tab === "dosen" && "Manajemen Dosen"}
                  {tab === "mahasiswa" && "Manajemen Mahasiswa"}
                  {tab === "timeslot" && "Manajemen Slot Waktu"}
                </p>
                <p className="text-sm text-gray-500">
                  Modul ini sedang dalam pengembangan
                </p>
              </div>
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};

export default AdminManagement;
