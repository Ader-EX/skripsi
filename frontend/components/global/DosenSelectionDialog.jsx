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

const DOSEN_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/dosen/get-dosen/names`;

const DosenSelectionDialog = ({ isOpen, onClose, onSelect }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [dosenList, setDosenList] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (isOpen) fetchDosen();
  }, [isOpen, page]);

  const handleSearch = () => {
    setPage(1);
    fetchDosen();
  };

  const fetchDosen = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, limit: 10 });
      if (searchTerm) params.append("filter", searchTerm);

      const response = await fetch(`${DOSEN_API_URL}?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch Dosen");

      const data = await response.json();
      setDosenList(data.data);
      setTotalPages(Math.ceil(data.total / 10));
    } catch (error) {
      console.error("Error fetching Dosen:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Pilih Dosen</DialogTitle>
        </DialogHeader>

        <div className="flex gap-2 mb-4">
          <Input
            type="text"
            placeholder="Cari Dosen..."
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
                <TableHead>ID Dosen</TableHead>
                <TableHead>Nama Dosen</TableHead>
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
                dosenList.map((dosen) => (
                  <TableRow key={dosen.id}>
                    <TableCell>{dosen.id}</TableCell>
                    <TableCell>{dosen.nama}</TableCell>
                    <TableCell>
                      <Button
                        className="bg-primary"
                        onClick={() => {
                          onSelect(dosen);
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
          <span className="text-sm">Halaman {page}</span>
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

export default DosenSelectionDialog;
