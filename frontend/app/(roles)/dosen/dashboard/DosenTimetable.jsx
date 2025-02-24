"use client";
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { decodeToken } from "@/utils/decoder";

const DosenTimetable = () => {
  const [timetableData, setTimetableData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(null);

  // Pagination
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [filter, setFilter] = useState("");

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Fetch user data and timetable when component mounts
    const fetchUserData = async () => {
      try {
        const token = Cookies.get("access_token");

        const decodedToken = decodeToken(token);
        setUserId(decodedToken.role_id);
        await fetchDosenTimetable(decodedToken.role_id);
      } catch (error) {
        toast.error("Gagal mengambil data dosen");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [page, filter]); // Refetch when `page` or `filter` changes

  const fetchDosenTimetable = async (dosenId) => {
    try {
      setLoading(true);
      const token = Cookies.get("access_token");

      const response = await fetch(
        `${BASE_URL}/dosen/timetable/${dosenId}?page=${page}&page_size=${limit}&filter=${filter}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Gagal mengambil jadwal dosen");

      const data = await response.json();
      setTimetableData(data.data);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      toast.error("Gagal mengambil jadwal dosen");
    } finally {
      setLoading(false);
    }
  };

  // Format Timeslot Display
  const formatSchedule = (schedule) => {
    if (!schedule) return "-";
    return schedule.replace("DayEnum.", "");
  };

  const handleSearchClick = () => {
    setFilter(searchInput);
    setPage(1);
  };

  return (
    <div className="w-full flex flex-col gap-y-4 mx-auto p-4">
      <div className="w-full flex justify-between">
        <h1 className="text-primary font-bold text-2xl">Jadwal Dosen</h1>
      </div>

      <Card className="bg-surface border-border">
        <CardHeader className="bg-primary text-primary-foreground p-4">
          <h2 className="text-lg font-semibold">Jadwal Mengajar</h2>
          <p className="text-sm opacity-90">
            Menampilkan daftar mata kuliah yang diajar oleh dosen
          </p>
        </CardHeader>
        <CardContent className="p-4">
          {/* Search Bar */}
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Cari berdasarkan nama atau kode mata kuliah"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)} // ✅ Updates input only
              className="w-full"
            />
            <Button
              onClick={handleSearchClick}
              className="bg-primary text-white"
            >
              <Search />
              Cari
            </Button>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table className="w-full border-collapse">
                <TableHeader>
                  <TableRow className="bg-primary/5">
                    <TableHead>Kode Mata Kuliah</TableHead>
                    <TableHead>Mata Kuliah</TableHead>
                    <TableHead>Kelas</TableHead>
                    <TableHead>SKS</TableHead>
                    <TableHead>Jadwal</TableHead>
                    <TableHead>Ruangan</TableHead>
                    <TableHead>Dosen</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {timetableData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan="7" className="p-8 text-center">
                        <p className="text-lg font-medium">
                          Belum ada jadwal untuk Anda
                        </p>
                        <p className="text-sm">
                          Silakan periksa kembali atau hubungi admin
                        </p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    timetableData.map((course) => (
                      <TableRow
                        key={course.timetable_id}
                        className="border-b border-border"
                      >
                        <TableCell>{course.kodemk}</TableCell>
                        <TableCell>{course.matakuliah}</TableCell>
                        <TableCell>{course.kelas}</TableCell>
                        <TableCell>{course.sks}</TableCell>
                        <TableCell>{formatSchedule(course.schedule)}</TableCell>
                        <TableCell>{course.ruangan}</TableCell>
                        <TableCell>{course.dosen}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}

          {/* Pagination */}
          <div className="flex justify-between items-center mt-4">
            <Button
              variant="outline"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="mr-2" /> Previous
            </Button>
            <span>
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((prev) => prev + 1)}
              disabled={page === totalPages}
            >
              Next <ChevronRight className="ml-2" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DosenTimetable;
