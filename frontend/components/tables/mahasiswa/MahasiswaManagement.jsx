"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Trash2, Search } from "lucide-react";
import MahasiswaTable from "./MahasiswaTable";
import MahasiswaForm from "./MahasiswaForm";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa`;
const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi`;

const MahasiswaManagement = () => {
  const token = Cookies.get("access_token");
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  const [mahasiswaList, setMahasiswaList] = useState([]);
  const [programStudiList, setProgramStudiList] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    semester: "all", // default to "all"
    program_studi_id: "all", // default to "all"
    search: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentMataKuliah, setCurrentMataKuliah] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchMahasiswa();
    fetchProgramStudi();
  }, [filters, page, pageSize]);

  /** Fetch Mahasiswa Data with Loading Overlay */
  const fetchMahasiswa = async () => {
    setLoading(true);
    try {
      setOverlayText("Memuat data mahasiswa...");
      setIsActive(true);
      let url = `${API_URL}/get-all?`;
      const queryParams = new URLSearchParams();
      if (filters.semester !== "all")
        queryParams.append("semester", filters.semester);
      if (filters.program_studi_id !== "all")
        queryParams.append("program_studi_id", filters.program_studi_id);
      if (filters.search) queryParams.append("search", filters.search);
      url += queryParams.toString();

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok)
        throw new Error(`Error fetching data: ${response.status}`);
      const data = await response.json();
      setMahasiswaList(data);
    } catch (error) {
      toast.error("Gagal mengambil data mahasiswa.");
      console.error("Error fetching mahasiswa:", error);
    } finally {
      setLoading(false);
      setIsActive(false);
    }
  };

  /** Fetch Program Studi Data with Loading Overlay */
  const fetchProgramStudi = async () => {
    try {
      setOverlayText("Memuat data program studi...");
      setIsActive(true);
      const response = await fetch(PROGRAM_STUDI_API_URL, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch program studi");
      const data = await response.json();
      setProgramStudiList(data);
    } catch (error) {
      toast.error("Gagal mengambil data program studi.");
      console.error("Error fetching program studi:", error);
    } finally {
      setIsActive(false);
    }
  };

  /** Open Form for Adding Mahasiswa */
  const handleAdd = () => {
    setEditData(null);
    setFormOpen(true);
  };

  /** Open Form for Editing Mahasiswa */
  const handleEdit = (data) => {
    setEditData(data);
    setFormOpen(true);
  };

  /** Open Delete Confirmation Modal */
  const handleDeleteClick = (id) => {
    setDeleteId(id);
    setDeleteModalOpen(true);
  };

  /** Confirm Deleting Mahasiswa & Associated User */
  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      const response = await fetch(`${API_URL}/${deleteId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to delete mahasiswa");
      toast.success("Mahasiswa berhasil dihapus");
      fetchMahasiswa();
    } catch (error) {
      toast.error("Gagal menghapus mahasiswa.");
      console.error("Error deleting mahasiswa:", error);
    } finally {
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Mahasiswa</span>
          <Button
            onClick={handleAdd}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="mr-2 h-4 w-4" />
            Tambah Mahasiswa
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <Label>Semester</Label>
            <Select
              value={filters.semester}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, semester: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Semester" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                {["1", "2", "3", "4", "5", "6", "7", "8"].map((sem) => (
                  <SelectItem key={sem} value={sem}>
                    Semester {sem}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Program Studi</Label>
            <Select
              value={filters.program_studi_id}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, program_studi_id: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Program Studi" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                {programStudiList.map((program) => (
                  <SelectItem key={program.id} value={program.id.toString()}>
                    {program.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Pencarian</Label>
            <Input
              type="text"
              placeholder="Cari nama atau NIM"
              value={filters.search}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, search: e.target.value }))
              }
            />
          </div>
        </div>

        {/* Mahasiswa Table */}
        <MahasiswaTable
          mahasiswaList={mahasiswaList}
          onEdit={handleEdit}
          onDelete={handleDeleteClick}
        />

        {/* Form Dialog for Add/Edit */}
        <MahasiswaForm
          isOpen={formOpen}
          onClose={() => setFormOpen(false)}
          onSubmit={fetchMahasiswa}
          initialData={editData}
        />
      </CardContent>

      {/* Delete Confirmation Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Hapus</DialogTitle>
          </DialogHeader>
          <p>Apakah Anda yakin ingin menghapus Mahasiswa ini?</p>
          <DialogFooter className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Batal
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Hapus
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default MahasiswaManagement;
