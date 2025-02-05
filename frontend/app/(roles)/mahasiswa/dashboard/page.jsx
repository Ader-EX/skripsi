"use client";
import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronLeft, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { decodeToken } from "@/utils/decoder";

const MahasiswaDashboard = () => {
  const [availableCourses, setAvailableCourses] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [error, setError] = useState(null);

  // Modal and pagination states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(5);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState("");
  const [selectedCourseToAdd, setSelectedCourseToAdd] = useState(null);

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchAvailableCourses = async (pageNumber = 1, filterText = "") => {
    try {
      const token = Cookies.get("access_token");
      const response = await fetch(
        `${BASE_URL}/algorithm/timetable?page=${pageNumber}&limit=${limit}&filter=${filterText}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to fetch courses");

      const data = await response.json();
      setAvailableCourses(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      toast.error("Failed to fetch available courses");
    } finally {
      setLoading(false);
    }
  };

  // ... (keep other existing methods like fetchUserData, fetchStudentTimetable, etc.)

  const openCourseSelectionModal = () => {
    setIsModalOpen(true);
    fetchAvailableCourses(1);
  };

  const handleCourseSelect = (course) => {
    setSelectedCourseToAdd(course);
  };

  const confirmCourseSelection = () => {
    if (selectedCourseToAdd) {
      // Check if course is already selected
      if (
        !selectedCourses.some((c) => c.Kodemk === selectedCourseToAdd.Kodemk)
      ) {
        setSelectedCourses([...selectedCourses, selectedCourseToAdd]);
        setIsModalOpen(false);
        setSelectedCourseToAdd(null);
      } else {
        toast.error("Course already selected");
      }
    }
  };

  const handleFilterChange = (e) => {
    const filterText = e.target.value;
    setFilter(filterText);
    fetchAvailableCourses(1, filterText);
  };

  const handlePageChange = (newPage) => {
    if (newPage > 0 && newPage <= totalPages) {
      setPage(newPage);
      fetchAvailableCourses(newPage, filter);
    }
  };

  return (
    <div className="w-full flex flex-col gap-y-4 mx-auto p-4">
      <h1 className="text-primary font-bold text-2xl">Dashboard</h1>

      {/* Existing Card Content */}
      <Card className="bg-surface border-border">
        <CardHeader className="bg-primary text-primary-foreground">
          <h2 className="text-lg font-semibold">
            Periode Pengisian KRS 2024/2025 Ganjil
          </h2>
          <p className="text-sm opacity-90">
            07 Agustus 2024 Pukul 15.00 WIB s/d 08 Aug 2024 Pukul 23.59 WIB
          </p>
        </CardHeader>
        <CardContent className="p-4">
          {/* Selected Courses Table */}
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
                {selectedCourses.length === 0 ? (
                  <tr>
                    <td
                      colSpan="6"
                      className="p-8 text-center text-text-secondary"
                    >
                      <div className="flex flex-col items-center justify-center space-y-2">
                        <p className="text-lg font-medium">
                          Belum ada mata kuliah yang dipilih
                        </p>
                        <p className="text-sm">
                          Silakan pilih mata kuliah dari dropdown di bawah
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  selectedCourses.map((course, index) => (
                    <tr
                      key={`${course.Kodemk}-${index}`}
                      className={`border-b border-border hover:bg-surface/80 transition-colors
                        ${index % 2 === 0 ? "bg-white" : "bg-surface"}`}
                    >
                      <td className="p-3 text-text-primary">
                        {course.Kodemk || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.Matakuliah || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.Kelas || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.Sks || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.Jadwal_Pertemuan || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.Dosen || "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Course Selection Section */}
          <div className="mt-6 space-y-4">
            <Button
              onClick={openCourseSelectionModal}
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Pilih Mata Kuliah
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Course Selection Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Pilih Mata Kuliah</DialogTitle>
          </DialogHeader>

          {/* Filter Input */}
          <div className="mb-4">
            <Input
              placeholder="Cari Mata Kuliah (Nama/Kode)"
              value={filter}
              onChange={handleFilterChange}
            />
          </div>

          {/* Courses Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Pilih</TableHead>
                <TableHead>Kode MK</TableHead>
                <TableHead>Mata Kuliah</TableHead>
                <TableHead>Kelas</TableHead>
                <TableHead>SKS</TableHead>
                <TableHead>Jadwal Pertemuan</TableHead>
                <TableHead>Dosen</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {availableCourses.map((course, index) => (
                <TableRow
                  key={`${course.Kodemk}-${index}`}
                  onClick={() => handleCourseSelect(course)}
                  className={`cursor-pointer ${
                    selectedCourseToAdd?.Kodemk === course.Kodemk
                      ? "bg-primary/10"
                      : "hover:bg-surface/50"
                  }`}
                >
                  <TableCell>
                    <input
                      type="radio"
                      checked={
                        selectedCourseToAdd?.timetable_id ===
                        course.timetable_id
                      }
                      onChange={() => handleCourseSelect(course)}
                    />
                  </TableCell>
                  <TableCell>{course.Kodemk}</TableCell>
                  <TableCell>{course.Matakuliah}</TableCell>
                  <TableCell>{course.Kelas}</TableCell>
                  <TableCell>{course.Sks}</TableCell>
                  <TableCell>{course.Jadwal_Pertemuan}</TableCell>
                  <TableCell>{course.Dosen}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          <div className="flex justify-between items-center mt-4">
            <Button
              variant="outline"
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
            >
              <ChevronLeft className="mr-2" /> Previous
            </Button>
            <span>
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              onClick={() => handlePageChange(page + 1)}
              disabled={page === totalPages}
            >
              Next <ChevronRight className="ml-2" />
            </Button>
          </div>

          {/* Modal Actions */}
          <div className="flex justify-end space-x-2 mt-4">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Batal
            </Button>
            <Button
              onClick={confirmCourseSelection}
              disabled={!selectedCourseToAdd}
            >
              Pilih Mata Kuliah
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MahasiswaDashboard;
