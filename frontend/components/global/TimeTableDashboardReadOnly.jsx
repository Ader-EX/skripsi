"use client";
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Eye, ChevronLeft, ChevronRight, Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import toast from "react-hot-toast";
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/formatted-timetable/`;

const TimeTableDashboardReadOnly = () => {
  const [scheduleList, setScheduleList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  // searchInput is updated on every keystroke
  const [searchInput, setSearchInput] = useState("");
  // appliedFilter is used to actually fetch the data
  const [appliedFilter, setAppliedFilter] = useState("");
  const [pageNumber, setPageNumber] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const token = Cookies.get("access_token");

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", pageNumber);
      // Use appliedFilter here so API is called with the search term only when applied
      if (appliedFilter) params.append("filterText", appliedFilter);

      const response = await fetch(`${API_URL}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch schedules");

      const data = await response.json();
      setScheduleList(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error("Error fetching schedules:", error);
      toast.error("Gagal mengambil jadwal");
    } finally {
      setLoading(false);
    }
  };

  // Only trigger fetching when pageNumber or appliedFilter changes
  useEffect(() => {
    fetchSchedules();
  }, [pageNumber, appliedFilter]);

  const handleSearch = () => {
    setPageNumber(1);
    // update the applied filter so the useEffect calls fetchSchedules
    setAppliedFilter(searchInput);
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle>Jadwal Kuliah</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Search Bar */}
        <div className="flex flex-col gap-4 mb-4">
          <Input
            type="text"
            placeholder="Cari mata kuliah atau dosen"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1"
          />
          <Button
            onClick={handleSearch}
            className="bg-primary hover:bg-primary/90"
          >
            <Search className="mr-2 h-4 w-4" />
            Cari
          </Button>
        </div>

        {/* Schedule Table */}
        <Table className="w-full">
          <TableHeader>
            <TableRow className="bg-primary/5">
              <TableHead>Mata Kuliah</TableHead>
              <TableHead>Kelas</TableHead>
              <TableHead>Dosen</TableHead>
              <TableHead>Hari</TableHead>
              <TableHead>Waktu</TableHead>
              <TableHead>Ruangan</TableHead>
              <TableHead>Kapasitas</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : scheduleList.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  Tidak ada jadwal ditemukan.
                </TableCell>
              </TableRow>
            ) : (
              scheduleList.map((schedule) => (
                <TableRow key={schedule.timetable_id || schedule.id}>
                  <TableCell>
                    <div>
                      <div>{schedule.subject?.name}</div>
                      <div className="text-xs text-gray-500">
                        {schedule.subject?.code}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{schedule.class}</TableCell>
                  <TableCell>
                    {schedule.lecturers
                      ?.map((lecturer) => lecturer.name)
                      .join(", ")}
                  </TableCell>
                  <TableCell>{schedule.timeslots[0]?.day || "-"}</TableCell>
                  <TableCell>
                    {schedule.timeslots.length > 0 &&
                      `${schedule.timeslots[0].startTime} - ${
                        schedule.timeslots[schedule.timeslots.length - 1]
                          .endTime
                      }`}
                  </TableCell>
                  <TableCell>
                    <div>
                      <div>{schedule.room?.code}</div>
                      <div className="text-xs text-gray-500">
                        Kapasitas: {schedule.room?.capacity}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {schedule.enrolled || "0"}/{schedule.capacity}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="icon"
                      variant="outline"
                      onClick={() => setSelectedSchedule(schedule)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        <div className="flex justify-between items-center mt-4">
          <Button
            disabled={pageNumber === 1}
            onClick={() => setPageNumber((prev) => Math.max(prev - 1, 1))}
            className="flex items-center"
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Sebelumnya
          </Button>
          <span className="text-sm">
            Halaman {pageNumber} dari {totalPages}
          </span>
          <Button
            disabled={pageNumber >= totalPages}
            onClick={() =>
              setPageNumber((prev) => Math.min(prev + 1, totalPages))
            }
            className="flex items-center"
          >
            Selanjutnya
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardContent>

      {/* Details Dialog */}
      <Dialog
        open={!!selectedSchedule}
        onOpenChange={(open) => {
          if (!open) setSelectedSchedule(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Detail Jadwal</DialogTitle>
          </DialogHeader>
          {selectedSchedule && (
            <div className="space-y-4">
              <p>
                <strong>Mata Kuliah:</strong> {selectedSchedule.subject?.name} (
                {selectedSchedule.subject?.code})
              </p>
              <p>
                <strong>Kelas:</strong> {selectedSchedule.class}
              </p>
              <p>
                <strong>Dosen:</strong>{" "}
                {selectedSchedule.lecturers
                  ?.map((lecturer) => lecturer.name)
                  .join(", ")}
              </p>
              <p>
                <strong>Hari & Waktu:</strong>{" "}
                {selectedSchedule.timeslots[0]?.day}{" "}
                {selectedSchedule.timeslots.length > 0 &&
                  `${selectedSchedule.timeslots[0].startTime} - ${
                    selectedSchedule.timeslots[
                      selectedSchedule.timeslots.length - 1
                    ].endTime
                  }`}
              </p>
              <p>
                <strong>Ruangan:</strong> {selectedSchedule.room?.code}{" "}
                (Kapasitas: {selectedSchedule.room?.capacity})
              </p>
              <p>
                <strong>Jumlah Mahasiswa:</strong> {selectedSchedule.enrolled} /{" "}
                {selectedSchedule.capacity}
              </p>
              <p>
                <strong>Placeholder:</strong>
              </p>
              <pre className="bg-gray-100 p-2 rounded">
                {selectedSchedule.placeholder}
              </pre>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setSelectedSchedule(null)}>Tutup</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default TimeTableDashboardReadOnly;
