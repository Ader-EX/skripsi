"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
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

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa`;
const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi`;

const MahasiswaManagement = () => {
  const [mahasiswaList, setMahasiswaList] = useState([]);
  const [programStudiList, setProgramStudiList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [filters, setFilters] = useState({
    semester: "",
    program_studi_id: "",
    search: "",
  });

  useEffect(() => {
    fetchMahasiswa();
    fetchProgramStudi();
  }, [filters]);

  const fetchMahasiswa = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();

      if (filters.semester) params.append("semester", filters.semester);
      if (filters.program_studi_id)
        params.append("program_studi_id", filters.program_studi_id);
      if (filters.search) params.append("search", filters.search);

      const url = `${API_URL}/get-all?${params.toString()}`;
      console.log("Fetching from:", url);

      const response = await fetch(url);
      if (!response.ok)
        throw new Error(`Error fetching data: ${response.status}`);

      const data = await response.json();
      console.log("Fetched Data:", data);

      setMahasiswaList(data);
    } catch (error) {
      console.error("Error fetching mahasiswa:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProgramStudi = async () => {
    try {
      const response = await fetch(PROGRAM_STUDI_API_URL);
      if (!response.ok) throw new Error("Failed to fetch program studi");
      const data = await response.json();
      setProgramStudiList(data);
    } catch (error) {
      console.error("Error fetching program studi:", error);
    }
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
      fetchMahasiswa();
    } catch (error) {
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
              <SelectContent className="bg-white">
                <SelectItem value="Semua">Semua</SelectItem>
                {["1", "2", "3", "4", "5", "6", "7", "8"].map((sem) => (
                  <SelectItem key={sem} value={sem}>
                    {sem}
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
                setFilters((prev) => ({
                  ...prev,
                  program_studi_id: value,
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Program Studi" />
              </SelectTrigger>
              <SelectContent>
                {programStudiList.map((program) => (
                  <SelectItem
                    className="bg-white"
                    key={program.id}
                    value={program.id.toString()}
                  >
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
              placeholder="Cari nama atau email"
              value={filters.search}
              onChange={(e) =>
                setFilters((prev) => ({
                  ...prev,
                  search: e.target.value,
                }))
              }
            />
          </div>
        </div>

        <MahasiswaTable
          mahasiswaList={mahasiswaList}
          onEdit={handleEdit}
          onDelete={handleDeleteClick}
        />

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
