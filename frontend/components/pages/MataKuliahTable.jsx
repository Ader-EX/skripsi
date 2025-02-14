import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, Search } from "lucide-react";
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
}) => {
  const handleSearchChange = (e) => {
    setFilters((prev) => ({ ...prev, search: e.target.value }));
  };

  return (
    <>
      <div className="flex gap-2 mb-4">
        <Input
          value={filters.search}
          onChange={handleSearchChange}
          placeholder="Cari Kode atau Nama MK"
        />
        <Button
          className="bg-secondary hover:bg-secondary/90"
          onClick={() => setPage(1)}
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
              <TableHead>Semester</TableHead>
              <TableHead>Kurikulum</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {matakuliah.map((mk) => (
              <TableRow key={mk.kodemk}>
                <TableCell>{mk.kodemk}</TableCell>
                <TableCell>{mk.namamk}</TableCell>
                <TableCell>{mk.sks}</TableCell>
                <TableCell>{mk.smt}</TableCell>
                <TableCell>{mk.kurikulum}</TableCell>
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
            ))}
          </TableBody>
        </Table>
      </div>
    </>
  );
};

export default MataKuliahTable;
