"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import TimeTableView from "./TimeTableView";
import toast from "react-hot-toast";

import TimeTableForm from "./TimeTableForm"; // Import the form component
import { useRouter } from "next/navigation";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/formatted-timetable/`;

const TimeTableManagement = () => {
  const router = useRouter();
  const [scheduleList, setScheduleList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [pageNumber, setPageNumber] = useState(1);
  const [searchParams, setSearchParams] = useState({
    limit: 10,
    filterText: "",
    isConflicted: null,
  });
  const [searchInput, setSearchInput] = useState("");

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", pageNumber);
      params.append("limit", searchParams.limit);

      if (searchParams.filterText) {
        params.append("filterText", searchParams.filterText);
      }

      if (searchParams.isConflicted !== null) {
        params.append("is_conflicted", searchParams.isConflicted);
      }

      const response = await fetch(`${API_URL}?${params.toString()}`);
      if (!response.ok) throw new Error("Failed to fetch schedules");

      const data = await response.json();
      setScheduleList(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error("Error fetching schedules:", error);
      toast.error("Failed to fetch schedules");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedules();
  }, [pageNumber, searchParams]);

  const handleSearch = () => {
    setSearchParams((prev) => ({ ...prev, filterText: searchInput }));
    setPageNumber(1);
  };

  const handleAdd = () => {
    router.push("/admin/data-manajemen/edit");
  };

  const handleEdit = (schedule) => {
    setSelectedSchedule(schedule);
    setFormOpen(true);
  };

  const handleFormSubmit = () => {
    fetchSchedules(); // Refresh schedules after adding or editing
    setFormOpen(false);
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Jadwal Kuliah</span>
          <Button
            onClick={handleAdd}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="mr-2 h-4 w-4" />
            Tambah Jadwal
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <Label>Pencarian</Label>
            <div className="flex gap-2">
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
          </div>
        </div>

        <TimeTableView
          scheduleList={scheduleList}
          onEdit={handleEdit}
          onDelete={() => {}}
          loading={loading}
        />

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

        {/* Form Dialog for Add/Edit */}
        <TimeTableForm
          isOpen={formOpen}
          onClose={() => setFormOpen(false)}
          initialData={selectedSchedule}
          onSubmit={handleFormSubmit}
        />
      </CardContent>
    </Card>
  );
};

export default TimeTableManagement;
