"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Trash2 } from "lucide-react";
import AcademicPeriodTable from "./AcademicPeriodTable";
import AcademicPeriodForm from "./AcademicPeriodForm";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import toast from "react-hot-toast";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/academic-period`;

const AcademicPeriodManagement = () => {
  const [academicPeriods, setAcademicPeriods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [activePeriod, setActivePeriod] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchAcademicPeriods();
    fetchActiveAcademicPeriod();
  }, []);

  const fetchAcademicPeriods = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL);
      const data = await response.json();
      setAcademicPeriods(data);
    } catch (error) {
      console.error("Error fetching academic periods:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveAcademicPeriod = async () => {
    try {
      const response = await fetch(`${API_URL}/active`);
      if (response.ok) {
        const data = await response.json();
        setActivePeriod(data);
      } else {
        setActivePeriod(null);
      }
    } catch (error) {
      console.error("Error fetching active academic period:", error);
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

  const handleDeleteClick = (id, isActive) => {
    if (isActive) {
      toast.error(
        "Tidak dapat menghapus periode akademik yang sedang aktif. Nonaktifkan terlebih dahulu."
      );
      return;
    }
    setDeleteId(id);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      await fetch(`${API_URL}/${deleteId}`, { method: "DELETE" });
      fetchAcademicPeriods();
      fetchActiveAcademicPeriod();
    } catch (error) {
      toast.error("Gagal menghapus periode akademik.");
      console.error("Error deleting academic period:", error);
    } finally {
      toast.success("Periode akademik berhasil dihapus.");
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
  };

  const handleActivate = async (id) => {
    try {
      await fetch(`${API_URL}/${id}/activate`, { method: "PUT" });
      fetchAcademicPeriods();
      fetchActiveAcademicPeriod();
    } catch (error) {
      console.error("Error activating academic period:", error);
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Periode Akademik</span>
          <Button
            onClick={handleAdd}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="mr-2 h-4 w-4" />
            Tambah Periode
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activePeriod ? (
          <div className="mb-4 p-3 bg-green-100 border-l-4 border-green-500 text-green-700">
            <strong>Periode Akademik Aktif:</strong> {activePeriod.tahun_ajaran}{" "}
            - Semester {activePeriod.semester}
          </div>
        ) : (
          <div className="mb-4 p-3 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
            <strong>Tidak ada periode akademik aktif saat ini.</strong>
          </div>
        )}

        <AcademicPeriodTable
          academicPeriods={academicPeriods}
          onEdit={handleEdit}
          onDelete={handleDeleteClick} // ✅ Use new delete function
          onActivate={handleActivate}
        />
        <AcademicPeriodForm
          isOpen={formOpen}
          onClose={() => setFormOpen(false)}
          onSubmit={() => {
            fetchAcademicPeriods();
            fetchActiveAcademicPeriod();
          }}
          initialData={editData}
        />
      </CardContent>

      {/* ✅ Delete Confirmation Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Hapus</DialogTitle>
          </DialogHeader>
          <p>Apakah Anda yakin ingin menghapus periode akademik ini?</p>
          <DialogFooter className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Batal
            </Button>
            <Button
              className="bg-red-500"
              variant="destructive"
              onClick={handleConfirmDelete}
            >
              Hapus
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default AcademicPeriodManagement;
