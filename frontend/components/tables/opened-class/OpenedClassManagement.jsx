"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, ChevronLeft, ChevronRight, Search, Trash } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { OpenedClassTable } from "./OpenedClassTable";
import Link from "next/link";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/opened-class`;

const OpenedClassManagement = () => {
  const [classList, setClassList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [pageNumber, setPageNumber] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentSearch, setCurrentSearch] = useState(""); // Active search term
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const limit = 10;
  const token = Cookies.get("access_token");

  // Get overlay controls from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  useEffect(() => {
    fetchClasses();
  }, [pageNumber, currentSearch]);

  const fetchClasses = async () => {
    setLoading(true);
    try {
      // Activate the loading overlay with a custom message
      setOverlayText("Memuat data kelas...");
      setIsActive(true);

      const params = new URLSearchParams({
        page: pageNumber,
        limit,
        search: currentSearch,
      });

      const response = await fetch(`${API_URL}/get-all?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch classes");

      const data = await response.json();
      setClassList(data.data || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
      setIsActive(false); // Hide the overlay
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPageNumber(1);
    setCurrentSearch(searchTerm);
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
      if (!response.ok) throw new Error("Failed to delete class");

      toast.success("Kelas berhasil dihapus");
      fetchClasses();
    } catch (error) {
      console.error("Error deleting class:", error);
    } finally {
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Kelas</span>
          <Button className="bg-primary hover:bg-primary/90">
            <Link href="/admin/data-manajemen/edit-opened" className="flex">
              <Plus className="mr-2 h-4 w-4" />
              Tambah Kelas
            </Link>
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSearch} className="flex gap-4 mb-4">
          <div className="flex-1">
            <Label>Pencarian</Label>
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Cari mata kuliah"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Button type="submit">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </form>

        {/* Class Table */}
        <OpenedClassTable
          classList={classList}
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

        {/* Delete Confirmation Modal */}
        <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Konfirmasi Hapus</DialogTitle>
            </DialogHeader>
            <p>Apakah Anda yakin ingin menghapus kelas ini?</p>
            <DialogFooter className="flex justify-end gap-2 mt-4">
              <Button
                variant="outline"
                onClick={() => setDeleteModalOpen(false)}
              >
                Batal
              </Button>
              <Button variant="destructive" onClick={handleConfirmDelete}>
                <Trash className="mr-2 h-4 w-4" />
                Hapus
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default OpenedClassManagement;
