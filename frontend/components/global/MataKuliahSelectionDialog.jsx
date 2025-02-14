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

const MATKUL_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/matakuliah/get-matakuliah/names`;

const MatakuliahSelectionDialog = ({ isOpen, onClose, onSelect }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [matakuliahList, setMatakuliahList] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) fetchMatakuliah();
  }, [isOpen, page, searchTerm]);

  const fetchMatakuliah = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (searchTerm) params.append("search", searchTerm);

      const response = await fetch(`${MATKUL_API_URL}?${params.toString()}`);
      if (!response.ok) throw new Error("Failed to fetch Matakuliah");

      const data = await response.json();
      setMatakuliahList(data.data || []); // Make sure data is an array
      setTotalPages(Math.ceil(data.total / 10));
    } catch (error) {
      console.error("Error fetching Matakuliah:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
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
          <Button onClick={() => setPage(1)} className="bg-primary">
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
                <TableHead>Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={3} className="text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : (
                (matakuliahList || []).map((mk) => (
                  <TableRow key={mk.kodemk}>
                    <TableCell>{mk.kodemk}</TableCell>
                    <TableCell>{mk.namamk}</TableCell>
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
