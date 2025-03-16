"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import DosenTable from "./DosenTable";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import DosenForm from "./DosenForm";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/dosen`;
const USER_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/user/users/`;

const DosenManagement = () => {
  const [dosenList, setDosenList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editData, setEditData] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const token = Cookies.get("access_token");

  // Get overlay controls from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  useEffect(() => {
    fetchDosen();
  }, [page, limit, search]);

  const fetchDosen = async () => {
    setLoading(true);
    try {
      // Activate overlay with custom message before fetch
      setOverlayText("Memuat data dosen...");
      setIsActive(true);

      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });
      if (search) params.append("search", search);

      const response = await fetch(`${API_URL}/get-all?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch dosen");

      const data = await response.json();
      setDosenList(data.data);
      setTotalPages(data.total_pages);
      setTotalRecords(data.total_records);
    } catch (error) {
      toast.error("Gagal mengambil data dosen.");
      console.error("Error fetching dosen:", error);
    } finally {
      setLoading(false);
      setIsActive(false); // Hide overlay after fetch completes
    }
  };

  const handleSearchClick = () => {
    setSearch(searchInput);
    setPage(1);
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
      const response = await fetch(`${API_URL}/${deleteId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to delete dosen");

      toast.success("Dosen dan user berhasil dihapus");
      fetchDosen();
    } catch (error) {
      toast.error("Gagal menghapus dosen.");
      console.error("Error deleting dosen:", error);
    } finally {
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
  };

  const handleFormSubmit = async (formData) => {
    try {
      let response;

      if (editData && editData.pegawai_id) {
        response = await fetch(`${API_URL}/${editData.pegawai_id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(formData),
        });
      } else {
        response = await fetch(API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(formData),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        if (editData) {
          toast.error(`Gagal mengupdate dosen: ${errorData.detail}`);
        } else {
          toast.error(`Gagal menambahkan dosen: ${errorData.detail}`);
        }
        return;
      }

      const responseData = await response.json();
      if (editData) {
        toast.success("Dosen berhasil diupdate");
      } else {
        toast.success(
          `Dosen berhasil ditambahkan dengan ID: ${responseData.dosen_id}`
        );
      }
      fetchDosen();
      setFormOpen(false);
    } catch (error) {
      console.error("Error submitting form:", error);
      toast.error("Terjadi kesalahan saat menyimpan data.");
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Dosen</span>
          <Button
            onClick={handleAdd}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="mr-2 h-4 w-4" />
            Tambah Dosen
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="col-span-3">
            <Label>Pencarian</Label>
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Cari berdasarkan nama atau email..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
              <Button onClick={handleSearchClick} className="bg-primary">
                <Search />
              </Button>
            </div>
          </div>
          <div>
            <Label>Per page</Label>
            <Select
              value={limit.toString()}
              onValueChange={(value) => setLimit(Number(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 30, 50].map((value) => (
                  <SelectItem key={value} value={value.toString()}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-center py-4">Loading...</div>
        ) : (
          <DosenTable
            dosenList={dosenList}
            onEdit={handleEdit}
            onDelete={handleDeleteClick}
          />
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-500">
            Showing {totalRecords === 0 ? 0 : (page - 1) * limit + 1} to{" "}
            {Math.min(page * limit, totalRecords)} of {totalRecords}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage((p) => p + 1)}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>

        <DosenForm
          isOpen={formOpen}
          onClose={() => setFormOpen(false)}
          onSubmit={handleFormSubmit}
          initialData={editData}
        />

        {/* Delete Confirmation Modal */}
        <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Konfirmasi Hapus</DialogTitle>
            </DialogHeader>
            <p>Apakah Anda yakin ingin menghapus Dosen ini?</p>
            <DialogFooter>
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

export default DosenManagement;
