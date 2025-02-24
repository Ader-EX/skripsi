"use client";
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import Cookies from "js-cookie";

const OPENED_CLASS_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/opened-class/get-all`;

const OpenedClassSelectionDialog = ({
  isOpen,
  onClose,
  onSelect,
  timetableFilter = false,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [openedClassList, setOpenedClassList] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (isOpen) fetchOpenedClasses();
  }, [isOpen, page, searchQuery]);

  const fetchOpenedClasses = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (searchQuery) params.append("search", searchQuery);

      const response = await fetch(
        `${OPENED_CLASS_API_URL}?${params.toString()}&no_timetable=${timetableFilter}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) throw new Error("Failed to fetch Opened Classes");

      const data = await response.json();
      setOpenedClassList(data.data || []);
      setTotalPages(data.total_pages || 1); // Ensure total_pages is used from API
    } catch (error) {
      console.error("Error fetching Opened Classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1); // Reset to the first page before searching
    setSearchQuery(searchTerm);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Pilih Kelas yang Dibuka</DialogTitle>
        </DialogHeader>

        {/* Search Input */}
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="Cari Mata Kuliah..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Button onClick={handleSearch} className="bg-primary">
            <Search className="mr-2 h-4 w-4" />
            Cari
          </Button>
        </div>

        {/* Table */}
        <div className="max-h-80 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Kode MK</TableHead>
                <TableHead>Nama MK</TableHead>
                <TableHead>Kelas</TableHead>
                <TableHead>Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : openedClassList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-gray-500">
                    Tidak ada kelas yang ditemukan.
                  </TableCell>
                </TableRow>
              ) : (
                openedClassList.map((oc) => (
                  <TableRow key={oc.id}>
                    <TableCell>{oc.id}</TableCell>
                    <TableCell>{oc.mata_kuliah.kode}</TableCell>
                    <TableCell>{oc.mata_kuliah.nama}</TableCell>
                    <TableCell>{oc.kelas}</TableCell>
                    <TableCell>
                      <Button
                        className="bg-primary"
                        onClick={() => {
                          onSelect(oc);
                          onClose();
                        }}
                      >
                        Pilih
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        <div className="flex justify-between items-center mt-4">
          <Button
            disabled={page === 1}
            onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Sebelumnya
          </Button>
          <span className="text-sm">
            Halaman {page} dari {totalPages}
          </span>
          <Button
            disabled={page >= totalPages}
            onClick={() => setPage((prev) => prev + 1)}
          >
            Selanjutnya
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Tutup
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default OpenedClassSelectionDialog;
