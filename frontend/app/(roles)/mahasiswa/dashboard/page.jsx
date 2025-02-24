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
  const [limit, setLimit] = useState(3);
  const [prodiId, setProdiId] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState("");
  const [selectedCourseToAdd, setSelectedCourseToAdd] = useState(null);

  const [isCoursesLoading, setIsCoursesLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchValue, setSearchValue] = useState("");

  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [currentSemester, setCurrentSemester] = useState(null);
  const [currentAcademicYear, setCurrentAcademicYear] = useState(null);
  const [weekStart, setWeekStart] = useState("");
  const [weekEnd, setWeekEnd] = useState("");
  const token = Cookies.get("access_token");

  const fetchAcademicPeriod = async () => {
    try {
      const response = await fetch(`${BASE_URL}/academic-period/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch academic period");

      const data = await response.json();
      setCurrentSemester(data.semester);
      setCurrentAcademicYear(data.tahun_ajaran.toString());
      setWeekStart(data.week_start);
      setWeekEnd(data.week_end);
    } catch (error) {
      console.error("Error fetching academic period:", error);
      toast.error("Gagal mendapatkan semester aktif");
    }
  };

  useEffect(() => {
    // Fetch user data on component mount
    const fetchUserData = async () => {
      try {
        const token = Cookies.get("access_token");
        if (!token) {
          throw new Error("No access token found");
        }

        const decodedToken = decodeToken(token);

        setUserId(decodedToken.role_id);
        setProdiId(decodedToken.prodi_id);
        await fetchStudentTimetable(decodedToken.role_id);
      } catch (error) {
        toast.error(
          "Failed to fetch user data, no datas present in the timeline"
        );
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
    fetchAcademicPeriod();
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

      // Format lecturers from the dosen string
      const formatLecturers = (dosenString) => {
        if (!dosenString) return [];
        return dosenString.split("\n").map((lecturer) => {
          const name = lecturer.replace(/^\d+\.\s*/, "").trim();
          return { name };
        });
      };

      // Ensure each course has proper structure and formatting
      const formattedData = data.data.map((course) => ({
        ...course,
        timetable_id: course.timetable_id || course.id,
        timeslots: Array.isArray(course.timeslots)
          ? course.timeslots.map((slot) => ({
              ...slot,
              startTime: slot.start_time,
              endTime: slot.end_time,
            }))
          : [],
        subject: {
          code: course.kodemk || "-",
          name: course.matakuliah || "-",
          sks: course.sks || "-",
          semester: course.semester || "-",
        },
        class: course.kelas || "-",
        capacity: course.sks || "-",
        lecturers: formatLecturers(course.dosen),
      }));

      setSelectedCourses(formattedData); // ✅ Updates UI **immediately**
    } catch (error) {
      console.error("Error fetching student timetable:", error);
      toast.error("Failed to fetch student timetable");
    }
  };

  // Update the formatTimeslots function to handle the new time format
  const formatTimeslots = (timeslots) => {
    if (!timeslots || !Array.isArray(timeslots) || timeslots.length === 0) {
      return "-";
    }

    // Filter out invalid timeslots and ensure all required properties exist
    const validTimeslots = timeslots.filter(
      (slot) =>
        slot &&
        slot.day &&
        (slot.startTime || slot.start_time) &&
        (slot.endTime || slot.end_time)
    );

    if (validTimeslots.length === 0) {
      return "-";
    }

    // Sort timeslots by startTime, with null-safe comparison
    const sortedTimeslots = [...validTimeslots].sort((a, b) => {
      const aTime = a.startTime || a.start_time;
      const bTime = b.startTime || b.start_time;
      if (!aTime) return 1;
      if (!bTime) return -1;
      return aTime.localeCompare(bTime);
    });

    const firstSlot = sortedTimeslots[0];
    const lastSlot = sortedTimeslots[sortedTimeslots.length - 1];

    // Handle both startTime/endTime and start_time/end_time formats
    const startTime = firstSlot.startTime || firstSlot.start_time;
    const endTime = lastSlot.endTime || lastSlot.end_time;

    return `${firstSlot.day} - ${startTime} to ${endTime}`;
  };

  const applySearch = () => {
    setFilter(searchValue); // Apply search when button is clicked
    fetchAvailableCourses(1, searchValue); // Call API with search value
  };

  const handleRemoveCourse = async (course, mahasiswa_id) => {
    const toastId = toast.loading("Menghapus jadwal...");

    try {
      const timetableId = course.timetable_id || course.id; // ✅ Ensure correct ID usage

      if (!timetableId) {
        throw new Error("Timetable ID is undefined");
      }

      const response = await fetch(
        `${BASE_URL}/mahasiswa-timetable/timetable/${mahasiswa_id}/${timetableId}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete timetable entry");
      }

      // ✅ Filter courses correctly
      setSelectedCourses((prevCourses) =>
        prevCourses.filter((c) => (c.timetable_id || c.id) !== timetableId)
      );

      toast.success("Jadwal berhasil dihapus", { id: toastId });
    } catch (error) {
      console.error("Error deleting course:", error);
      toast.error("Terjadi kesalahan saat menghapus jadwal", { id: toastId });
    }
  };

  const fetchAvailableCourses = async (pageNumber = 1, filterText = "") => {
    try {
      setIsCoursesLoading(true);
      const token = Cookies.get("access_token");
      const response = await fetch(
        `${BASE_URL}/algorithm/formatted-timetable?page=${pageNumber}&limit=${limit}&filterText=${filterText}&program_studi_id=${prodiId}`,
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

  const openCourseSelectionModal = async () => {
    setIsModalOpen(true);
    await fetchAcademicPeriod();
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

    const selectedKodemk = selectedCourseToAdd.subject?.code;
    const selectedClass = selectedCourseToAdd.class;

    // Prevent selecting the same kodemk with different classes
    const isDuplicateKodemk = selectedCourses.some(
      (course) =>
        course.subject?.code === selectedKodemk &&
        course.class !== selectedClass
    );

    if (isDuplicateKodemk) {
      toast.error(
        `Anda sudah mengambil mata kuliah ${selectedKodemk} dengan kelas yang berbeda`
      );
      return;
    }

    const selectedSubjectName = selectedCourseToAdd.subject?.name.toLowerCase();
    const isRelatedCourseTaken = selectedCourses.some(
      (course) =>
        course.subject?.name
          .toLowerCase()
          .includes(selectedSubjectName.replace("praktikum", "").trim()) &&
        course.class !== selectedClass
    );

    if (isRelatedCourseTaken) {
      toast.error(
        `Anda sudah mengambil mata kuliah terkait dengan ${selectedCourseToAdd.subject?.name}, pastikan kelasnya sama (${selectedClass})`
      );
      return;
    }

    try {
      setIsSubmitting(true);
      const token = Cookies.get("access_token");

      const periodResponse = await fetch(`${BASE_URL}/academic-period/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!periodResponse.ok) {
        throw new Error("Gagal mendapatkan periode akademik aktif");
      }

      const periodData = await periodResponse.json();
      const academicPeriodId = periodData.id;
      const response = await fetch(`${BASE_URL}/mahasiswa-timetable/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          mahasiswa_id: Number(userId),
          timetable_id: selectedCourseToAdd.id,
          academic_period_id: academicPeriodId, // ✅ Use academic period ID
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add course");
      }

      const addedCourse = await response.json();
      setSelectedCourses([...selectedCourses, selectedCourseToAdd]);
      toast.success("Mata kuliah berhasil ditambahkan");

      setIsModalOpen(false);
      setSelectedCourseToAdd(null);

      await fetchStudentTimetable(userId);
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
            Periode Pengisian KRS {currentAcademicYear}/
            {Number(currentAcademicYear) + 1}{" "}
            {currentSemester === 1 ? "Ganjil" : "Genap"}
          </h2>
          <p className="text-sm opacity-90">
            {weekStart && weekEnd
              ? `${new Date(weekStart).toLocaleDateString()} s/d ${new Date(
                  weekEnd
                ).toLocaleDateString()}`
              : "Loading tanggal..."}
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
                    Semester
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
                          Silakan pilih mata kuliah dari daftar di bawah
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  selectedCourses.map((course, index) => {
                    return (
                      <tr
                        key={
                          course.timetable_id || course.id || `course-${index}`
                        }
                        className={`border-b border-border hover:bg-surface/80 transition-colors ${
                          index % 2 === 0 ? "bg-white" : "bg-surface"
                        }`}
                      >
                        <td className="p-3 text-text-primary">
                          {course.subject?.code || "-"}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.subject?.name || "-"}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.class || "-"}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.sks || course.capacity || "-"}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.smt || "-"}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.placeholder}
                        </td>
                        <td className="p-3 text-text-primary">
                          {course.lecturers
                            ?.map((lecturer) => lecturer.name)
                            .join(", ") || "-"}
                        </td>
                        <td className="p-3">
                          <Trash
                            onClick={() => handleRemoveCourse(course, userId)}
                            className="text-red-600 size-4 cursor-pointer"
                          />
                        </td>
                      </tr>
                    );
                  })
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
              onChange={(e) => setSearchValue(e.target.value)}
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
                    <TableHead>Kelas</TableHead>
                    <TableHead>SKS</TableHead>
                    <TableHead>Semester</TableHead>
                    <TableHead>Jadwal Pertemuan</TableHead>
                    <TableHead>Dosen</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {availableCourses.map((course, index) => (
                    <TableRow
                      key={course.id}
                      onClick={() => handleCourseSelect(course)}
                      className={`cursor-pointer ${
                        selectedCourseToAdd?.id === course.id
                          ? "bg-primary/10"
                          : "hover:bg-surface/50"
                      }`}
                    >
                      <TableCell>
                        <input
                          type="radio"
                          checked={selectedCourseToAdd?.id === course.id}
                          onChange={() => handleCourseSelect(course)}
                        />
                      </TableCell>

                      {/* ✅ Correctly displaying subject code & name */}
                      <TableCell>{course.subject?.code || "-"}</TableCell>
                      <TableCell>{course.subject?.name || "Unknown"}</TableCell>

                      <TableCell>{course.class || "-"}</TableCell>
                      <TableCell>{course.subject?.sks || "-"}</TableCell>
                      <TableCell>{course.subject?.semester || "-"}</TableCell>

                      {/* ✅ Properly formatted Timeslot */}
                      <TableCell>{formatTimeslots(course.timeslots)}</TableCell>

                      {/* ✅ Properly formatted Lecturers */}
                      <TableCell>
                        {course.lecturers
                          ?.map((lecturer) => lecturer.name)
                          .join(", ") || "-"}
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
