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
import { ChevronLeft, ChevronRight, Plus, Search, Trash } from "lucide-react";
import { Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { decodeToken } from "@/utils/decoder";

const MahasiswaDashboard = () => {
  const [availableCourses, setAvailableCourses] = useState([]);
  const [selectedCourses, setSelectedCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState(null);

  const [error, setError] = useState(null);

  // Modal and pagination states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(5);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState("");
  const [selectedCourseToAdd, setSelectedCourseToAdd] = useState(null);

  // New loading states
  const [isCoursesLoading, setIsCoursesLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchValue, setSearchValue] = useState("");

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Fetch user data on component mount
    const fetchUserData = async () => {
      try {
        const token = Cookies.get("access_token");
        if (!token) {
          throw new Error("No access token found");
        }

        const decodedToken = decodeToken(token);

        const details = await fetch(
          `${BASE_URL}/user/details?email=${decodedToken.sub}`
        );
        const data = await details.json();
        if (!details.ok) {
          throw new Error("Failed to fetch user details");
        }
        console.log(data);
        setUserId(data.id);

        // Fetch existing timetable for the student
        await fetchStudentTimetable(data.id);
      } catch (error) {
        toast.error("Failed to fetch user data");
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const fetchStudentTimetable = async (mahasiswaId) => {
    try {
      const token = Cookies.get("access_token");
      const response = await fetch(
        `${BASE_URL}/mahasiswa-timetable/timetable/${mahasiswaId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) throw new Error("Failed to fetch student timetable");

      const data = await response.json();
      // Assuming the response contains timetable entries
      // Map the data to match your course structure if needed
      console.log(data.data);
      setSelectedCourses(data.data);
    } catch (error) {
      toast.error("Failed to fetch student timetable");
    }
  };
  const applySearch = () => {
    setFilter(searchValue); // Apply search when button is clicked
    fetchAvailableCourses(1, searchValue); // Call API with search value
  };

  const fetchAvailableCourses = async (pageNumber = 1, filterText = "") => {
    try {
      setIsCoursesLoading(true);
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
      setIsCoursesLoading(false);
    }
  };

  const openCourseSelectionModal = () => {
    setIsModalOpen(true);
    fetchAvailableCourses(1);
  };

  const handleCourseSelect = (course) => {
    setSelectedCourseToAdd(course);
  };

  const confirmCourseSelection = async () => {
    if (!selectedCourseToAdd) {
      toast.error("Silakan pilih mata kuliah terlebih dahulu");
      return;
    }
    let currentSemester;
    let currentAcademicYear;

    try {
      setIsSubmitting(true);
      const token = Cookies.get("access_token");

      try {
        const response = await fetch(
          "http://localhost:8000/academic-period/active"
        );
        if (!response.ok) throw new Error("No active period found");

        const data = await response.json();
        currentSemester = data.semester;
        currentAcademicYear = data.tahun_ajaran;

        console.log("Active Semester:", currentSemester);
        console.log("Active Academic Year:", currentAcademicYear);
      } catch (error) {
        console.error("Error fetching academic period:", error);
      }

      const response = await fetch(`${BASE_URL}/mahasiswa-timetable/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          mahasiswa_id: userId,
          timetable_id: selectedCourseToAdd.timetable_id,
          semester: currentSemester,
          tahun_ajaran: currentAcademicYear,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add course");
      }

      // Add the selected course to the local state
      setSelectedCourses([...selectedCourses, selectedCourseToAdd]);
      toast.success("Mata kuliah berhasil ditambahkan");

      // Close the modal and reset the selected course
      setIsModalOpen(false);
      setSelectedCourseToAdd(null);
    } catch (error) {
      toast.error(error.message || "Gagal menambahkan mata kuliah");
    } finally {
      setIsSubmitting(false);
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

  // Remove a selected course
  const removeCourse = (courseToRemove) => {
    setSelectedCourses(
      selectedCourses.filter(
        (course) => course.kodemk !== courseToRemove.kodemk
      )
    );
  };

  return (
    <div className="w-full flex flex-col gap-y-4 mx-auto p-4">
      <div className="w-full flex justify-between">
        <h1 className="text-primary font-bold text-2xl">Dashboard</h1>
        <Button
          onClick={openCourseSelectionModal}
          className=" bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Plus /> Pilih Mata Kuliah
        </Button>
      </div>

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
                    Kode Mata Kuliah
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
                  <th className="p-3 text-left text-text-primary font-semibold">
                    Aksi
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedCourses.length === 0 ? (
                  <tr>
                    <td
                      colSpan="7"
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
                      key={`${course.kodemk}-${index}`}
                      className={`border-b border-border hover:bg-surface/80 transition-colors
                        ${index % 2 === 0 ? "bg-white" : "bg-surface"}`}
                    >
                      <td className="p-3 text-text-primary">
                        {course.kodemk || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.matakuliah || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.kelas || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.sks || "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.timeslots[0].day} {" - "}
                        {course.timeslots.length > 0
                          ? `${course.timeslots[0].start_time} - ${
                              course.timeslots[course.timeslots.length - 1]
                                .end_time
                            }`
                          : "-"}
                      </td>
                      <td className="p-3 text-text-primary">
                        {course.dosen.split("\n").map((dosen, index) => (
                          <div key={index}>{dosen}</div>
                        ))}
                      </td>
                      <td className="p-3">
                        <Trash
                          onClick={() => removeCourse(course)}
                          className="text-red-600 size-4 cursor-pointer"
                        />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Course Selection Section */}

          <ol className="text-sm text-text-secondary mt-4">
            <li>
              1. Pastikan mata kuliah yang dipilih tidak memiliki jadwal yang
              bentrok.
            </li>
            <li>
              2. Klik ikon tong sampah untuk menghapus mata kuliah yang sudah
              dipilih.
            </li>
            <li>
              3. Periksa kembali total SKS yang telah dipilih agar tidak
              melebihi batas maksimal.
            </li>
            <li>
              4. Pastikan mata kuliah yang dipilih sesuai dengan rencana studi
              Anda.
            </li>
            <li>
              5. Simpan perubahan setelah memastikan semua mata kuliah sudah
              benar.
            </li>
          </ol>
        </CardContent>
      </Card>

      {/* Course Selection Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Pilih Mata Kuliah</DialogTitle>
          </DialogHeader>

          {/* Filter Input */}
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Cari Mata Kuliah (Nama/Kode)"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)} // Only updates local state
              className="w-full"
            />
            <Button onClick={applySearch} className="bg-primary text-white">
              <Search />
              Cari
            </Button>
          </div>

          {/* Courses Table */}
          {isCoursesLoading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Pilih</TableHead>
                    <TableHead>Kode MK</TableHead>
                    <TableHead>Mata Kuliah</TableHead>
                    <TableHead>kelas</TableHead>
                    <TableHead>SKS</TableHead>
                    <TableHead>Jadwal Pertemuan</TableHead>
                    <TableHead>dosen</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {availableCourses.map((course, index) => (
                    <TableRow
                      key={`${course.kodemk}-${index}`}
                      onClick={() => handleCourseSelect(course)}
                      className={`cursor-pointer ${
                        selectedCourseToAdd?.kodemk === course.kodemk
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
                      <TableCell>{course.kodemk}</TableCell>
                      <TableCell>{course.matakuliah}</TableCell>
                      <TableCell>{course.kelas}</TableCell>
                      <TableCell>{course.sks}</TableCell>
                      <TableCell>
                        {course.timeslots[0].day} {" - "}
                        {course.timeslots.length > 0
                          ? `${course.timeslots[0].start_time} - ${
                              course.timeslots[course.timeslots.length - 1]
                                .end_time
                            }`
                          : "-"}
                      </TableCell>
                      <TableCell>
                        {course.dosen.split("\n").map((dosen, index) => (
                          <div key={index}>{dosen}</div>
                        ))}
                      </TableCell>
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
            </>
          )}

          {/* Modal Actions */}
          <div className="flex justify-end space-x-2 mt-4">
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>
              Batal
            </Button>
            <Button
              onClick={confirmCourseSelection}
              disabled={!selectedCourseToAdd || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Menyimpan...
                </>
              ) : (
                "Pilih Mata Kuliah"
              )}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MahasiswaDashboard;
