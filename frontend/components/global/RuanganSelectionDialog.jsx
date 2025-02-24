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

const RUANGAN_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/ruangan`;

const RuanganSelectionDialog = ({ isOpen, onClose, onSelect }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchQuery, setSearchQuery] = useState(""); // Search is applied only when button is clicked
  const [ruanganList, setRuanganList] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (isOpen) fetchRuangan();
  }, [isOpen, page, searchQuery]);

  const fetchRuangan = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (searchQuery) params.append("name", searchQuery);

      const response = await fetch(`${RUANGAN_API_URL}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch Ruangan");

      const data = await response.json();
      setRuanganList(data.data || []);
      setTotalPages(Math.ceil((data.total || 1) / 10));
    } catch (error) {
      console.error("Error fetching Ruangan:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1); // Reset to the first page when searching
    setSearchQuery(searchTerm);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Pilih Ruangan</DialogTitle>
        </DialogHeader>

        {/* Search Input */}
        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="Cari Ruangan..."
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
                <TableHead>Nama Ruangan</TableHead>
                <TableHead>Gedung</TableHead>
                <TableHead>Kapasitas</TableHead>
                <TableHead>Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : ruanganList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-gray-500">
                    Tidak ada ruangan yang ditemukan.
                  </TableCell>
                </TableRow>
              ) : (
                ruanganList.map((ruangan) => (
                  <TableRow key={ruangan.id}>
                    <TableCell>{ruangan.nama_ruang}</TableCell>
                    <TableCell>{ruangan.gedung}</TableCell>
                    <TableCell>{ruangan.kapasitas}</TableCell>
                    <TableCell>
                      <Button
                        className="bg-primary"
                        onClick={() => {
                          onSelect(ruangan);
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
            disabled={page >= totalPages || ruanganList.length === 0}
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

export default RuanganSelectionDialog;
