"use client";
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const MahasiswaTimeTableManagement = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [mahasiswaList, setMahasiswaList] = useState([]);
  const [selectedMahasiswa, setSelectedMahasiswa] = useState(null);
  const [timetableList, setTimetableList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const token = Cookies.get("access_token");

  // Get overlay functions from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  useEffect(() => {
    if (selectedMahasiswa?.id) {
      fetchTimetables();
    }
  }, [selectedMahasiswa]);

  const fetchMahasiswa = async () => {
    try {
      setIsLoading(true);
      setOverlayText("Memuat data mahasiswa...");
      setIsActive(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa/get-mahasiswa?page=1&limit=10&search=${searchTerm}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch mahasiswa data");
      }

      const data = await response.json();
      setMahasiswaList(data.data || []);
    } catch (error) {
      console.error("Error fetching mahasiswa:", error);
      setError("Failed to fetch mahasiswa list");
      setMahasiswaList([]);
    } finally {
      setIsLoading(false);
      setIsActive(false);
    }
  };

  const fetchTimetables = async () => {
    if (!selectedMahasiswa?.id) return;
    try {
      setIsLoading(true);
      setOverlayText("Memuat jadwal mahasiswa...");
      setIsActive(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa-timetable/timetable/${selectedMahasiswa.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch timetable data");
      }

      const data = await response.json();

      if (!data.data || !Array.isArray(data.data)) {
        throw new Error("Invalid timetable data format");
      }

      setTimetableList(data.data);
    } catch (error) {
      console.error("Error fetching timetables:", error);
      setError("Failed to fetch timetable data");
      setTimetableList([]);
    } finally {
      setIsLoading(false);
      setIsActive(false);
    }
  };

  const handleInputClick = () => {
    setIsModalOpen(true);
    setError(null);
    fetchMahasiswa();
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setError(null);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchMahasiswa();
  };

  const handleSelectMahasiswa = (mahasiswa) => {
    setSelectedMahasiswa(mahasiswa);
    setIsModalOpen(false);
    setError(null);
  };

  const formatTimeRange = (startTime, endTime) => {
    return `${startTime} - ${endTime}`;
  };

  return (
    <div className="space-y-4">
      {/* Input Field for Selecting Mahasiswa */}
      <div>
        <Label>Pilih Mahasiswa</Label>
        <Input
          value={selectedMahasiswa ? selectedMahasiswa.fullname : ""}
          readOnly
          onClick={handleInputClick}
          placeholder="Klik untuk memilih mahasiswa..."
          className="cursor-pointer"
        />
      </div>

      {/* Dialog for Searching Mahasiswa */}
      <Dialog open={isModalOpen} onOpenChange={handleModalClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Select Mahasiswa</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <form onSubmit={handleSearch} className="space-y-2">
              <Label>Search Mahasiswa</Label>
              <div className="flex gap-2">
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Enter name to search..."
                />
                <Button type="submit">Search</Button>
              </div>
            </form>

            {isLoading && <div className="text-center py-4">Loading...</div>}

            {error && <div className="text-red-500 text-sm">{error}</div>}

            {!isLoading && mahasiswaList.length === 0 && !error && (
              <div className="text-center py-4 text-gray-500">
                No mahasiswa found
              </div>
            )}

            {mahasiswaList.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>NIM</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mahasiswaList.map((mahasiswa) => (
                    <TableRow key={mahasiswa.id}>
                      <TableCell>{mahasiswa.id}</TableCell>
                      <TableCell>{mahasiswa.fullname}</TableCell>
                      <TableCell>{mahasiswa.user_id}</TableCell>
                      <TableCell>
                        <Button
                          className="border bg-white text-blue-500 border-blue-500"
                          onClick={() => handleSelectMahasiswa(mahasiswa)}
                        >
                          Select
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Table is always visible, even when no mahasiswa is selected */}
      <div className="p-4 border rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Timetable:</h3>

        {isLoading && (
          <div className="text-center py-4">Loading timetable...</div>
        )}

        {error && <div className="text-red-500 text-sm">{error}</div>}

        {!isLoading && timetableList.length === 0 && !error && (
          <div className="text-center py-4 text-gray-500">
            No timetable entries found
          </div>
        )}

        {timetableList.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kode MK</TableHead>
                <TableHead>Mata Kuliah</TableHead>
                <TableHead>SKS</TableHead>
                <TableHead>Kelas</TableHead>
                <TableHead>Dosen</TableHead>
                <TableHead>Schedule</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {timetableList.map((subject) => (
                <TableRow key={subject.timetable_id}>
                  <TableCell>{subject.kodemk}</TableCell>
                  <TableCell>{subject.matakuliah}</TableCell>
                  <TableCell>{subject.sks}</TableCell>
                  <TableCell>{subject.kelas}</TableCell>
                  <TableCell className="whitespace-pre-line">
                    {subject.dosen}
                  </TableCell>
                  <TableCell>
                    <div className="space-y-1">
                      {subject.timeslots.map((slot) => (
                        <div key={slot.id} className="text-sm">
                          {slot.day}:{" "}
                          {formatTimeRange(slot.start_time, slot.end_time)}
                        </div>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
};

export default MahasiswaTimeTableManagement;
