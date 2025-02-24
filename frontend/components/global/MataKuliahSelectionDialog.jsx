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

const MatakuliahSelectionDialog = ({
  isOpen,
  onClose,
  onSelect,
  url = "/matakuliah/get-matakuliah/names",
}) => {
  const MATKUL_API_URL = `${process.env.NEXT_PUBLIC_API_URL}${url}`;

  const [searchTerm, setSearchTerm] = useState("");
  const [matakuliahList, setMatakuliahList] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (isOpen) fetchMatakuliah();
  }, [isOpen, page]);

  const handleSearch = () => {
    setPage(1);
    fetchMatakuliah();
  };

  const fetchMatakuliah = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (searchTerm) params.append("search", searchTerm);

      const response = await fetch(`${MATKUL_API_URL}?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch Matakuliah");

      const data = await response.json();
      setMatakuliahList(data.data || []);
      setTotalPages(Math.ceil(data.total / 10));
    } catch (error) {
      console.error("Error fetching Matakuliah:", error);
    } finally {
      setLoading(false);
    }
  };

  const getTipeMKLabel = (tipe) => {
    const mapping = {
      T: "Teori",
      P: "Praktikum",
      S: "Spesial",
    };
    return mapping[tipe] || "Unknown";
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>Pilih Mata Kuliah</DialogTitle>
        </DialogHeader>

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

        <div className="max-h-80 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Kode MK</TableHead>
                <TableHead>Nama MK</TableHead>
                <TableHead>Tipe MK</TableHead>
                <TableHead>SKS</TableHead>
                <TableHead>Kelas Besar?</TableHead>
                <TableHead>Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : !loading && matakuliahList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center p-8 h-10">
                    Semua Kelas Sudah Memiliki Timetable, silahkan Hapus Data
                    yang telah ada terlebih dahulu
                  </TableCell>
                </TableRow>
              ) : (
                matakuliahList.map((mk) => (
                  <TableRow key={mk.kodemk}>
                    <TableCell>{mk.kodemk}</TableCell>
                    <TableCell>{mk.namamk}</TableCell>
                    <TableCell>{getTipeMKLabel(mk.tipe_mk)}</TableCell>
                    <TableCell>{mk.sks}</TableCell>
                    <TableCell>
                      {mk.have_kelas_besar ? "Ya" : "Tidak"}
                    </TableCell>
                    <TableCell>
                      <Button
                        className="bg-primary"
                        onClick={() => {
                          onSelect(mk);
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

export default MatakuliahSelectionDialog;
