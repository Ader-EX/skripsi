"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, ChevronLeft, ChevronRight, Search } from "lucide-react";
import TimeTableForm from "./TimeTableForm";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import TimeTableView from "./TimeTableView";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/formatted-timetable`;

const TimeTableManagement = () => {
  const [scheduleList, setScheduleList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [totalPages, setTotalPages] = useState(1);
  const [pageNumber, setPageNumber] = useState(1);
  const limit = 10;

  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState("");

  useEffect(() => {
    fetchSchedules();
  }, [activeSearch, pageNumber]);

  const fetchSchedules = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append("page", pageNumber);
      params.append("limit", limit);
      if (activeSearch) params.append("filterText", activeSearch);

      const response = await fetch(`${API_URL}?${params.toString()}`);
      if (!response.ok) throw new Error("Failed to fetch schedules");

      const data = await response.json();
      setScheduleList(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error("Error fetching schedules:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setActiveSearch(searchTerm);
    setPageNumber(1);
  };

  const handleAdd = () => {
    setEditData(null);
    setFormOpen(true);
  };

  const handleEdit = (data) => {
    setEditData(data);
    setFormOpen(true);
  };

  const handleDeleteClick = (id) => {
    setDeleteId(id);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      await fetch(`${API_URL}/${deleteId}`, { method: "DELETE" });
      fetchSchedules();
    } catch (error) {
      console.error("Error deleting schedule:", error);
    } finally {
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
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
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearch();
                }}
              />
              <Button onClick={handleSearch}>
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        <TimeTableView
          scheduleList={scheduleList}
          onEdit={handleEdit}
          onDelete={handleDeleteClick}
          loading={loading}
        />

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

        <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Konfirmasi Hapus</DialogTitle>
            </DialogHeader>
            <p>Apakah Anda yakin ingin menghapus jadwal ini?</p>
            <DialogFooter className="flex justify-end gap-2 mt-4">
              <Button
                variant="outline"
                onClick={() => setDeleteModalOpen(false)}
              >
                Batal
              </Button>
              <Button variant="destructive" onClick={handleConfirmDelete}>
                Hapus
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default TimeTableManagement;
