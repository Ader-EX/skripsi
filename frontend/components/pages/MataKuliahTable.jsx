import React, { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  Pencil,
  Trash2,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Input } from "@/components/ui/input";

const MataKuliahTable = ({
  matakuliah,
  total,
  filters,
  setFilters,
  page,
  setPage,
  pageSize,
  setPageSize,
  handleDelete,
  handleEdit,
  fetchMataKuliah, // Fetch function passed from parent
}) => {
  const totalPages = Math.ceil(total / pageSize); // Calculate total pages
  const [searchQuery, setSearchQuery] = useState(filters.search || ""); // Local state for input

  const handleSearch = () => {
    setFilters((prev) => ({ ...prev, search: searchQuery }));
    setPage(1);
    fetchMataKuliah();
  };

  return (
    <>
      <div className="flex gap-2 mb-4">
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Cari Kode atau Nama MK"
        />
        <Button
          className="bg-secondary hover:bg-secondary/90"
          onClick={handleSearch} // 🔥 Only triggers search when button is clicked
        >
          <Search className="h-4 w-4" />
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow className="bg-primary/5">
              <TableHead>Kode</TableHead>
              <TableHead>Nama</TableHead>
              <TableHead>SKS</TableHead>
              <TableHead>Program Studi</TableHead>
              <TableHead>Semester</TableHead>
              <TableHead>Tipe</TableHead>
              <TableHead>Kelas Besar</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {matakuliah.length > 0 ? (
              matakuliah.map((mk) => (
                <TableRow key={mk.kodemk}>
                  <TableCell>{mk.kodemk}</TableCell>
                  <TableCell>{mk.namamk}</TableCell>
                  <TableCell>{mk.sks}</TableCell>
                  <TableCell>{mk.program_studi_name}</TableCell>
                  <TableCell>{mk.smt}</TableCell>
                  <TableCell>
                    <span
                      className={`px-2 py-1 rounded-full text-white ${
                        mk.tipe_mk === "T"
                          ? "bg-blue-500"
                          : mk.tipe_mk === "P"
                          ? "bg-orange-500"
                          : "bg-green-500"
                      }`}
                    >
                      {mk.tipe_mk === "T"
                        ? "Teori"
                        : mk.tipe_mk === "P"
                        ? "Praktikum"
                        : "Spesial"}
                    </span>
                  </TableCell>
                  <TableCell>{mk.have_kelas_besar ? "Ya" : "Tidak"}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="icon"
                      className="text-blue-500"
                      onClick={() => handleEdit(mk)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="text-red-500"
                      onClick={() => handleDelete(mk.kodemk)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-4">
                  Tidak ada data yang tersedia.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* ✅ Pagination Controls */}
      <div className="flex justify-between items-center mt-4">
        <div className="flex items-center gap-2">
          <span className="text-sm">
            Menampilkan {matakuliah.length} dari {total} data
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Previous Page */}
          <Button
            onClick={() => setPage(page - 1)}
            disabled={page === 1}
            variant="outline"
            size="sm"
          >
            <ChevronLeft className="h-4 w-4" />
            Prev
          </Button>

          {/* Page Number Display */}
          <span className="text-sm">
            Halaman {page} dari {totalPages}
          </span>

          {/* Next Page */}
          <Button
            onClick={() => setPage(page + 1)}
            disabled={page >= totalPages}
            variant="outline"
            size="sm"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* Page Size Selector */}
          <select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            className="ml-2 border rounded px-2 py-1 text-sm"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>
    </>
  );
};

export default MataKuliahTable;
