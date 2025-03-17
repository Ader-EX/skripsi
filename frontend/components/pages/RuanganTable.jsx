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
import { Pencil, Trash2 } from "lucide-react";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

const RuanganTable = ({
  ruangan,
  total,
  loading,
  filters,
  setFilters,
  page,
  setPage,
  pageSize,
  setPageSize,
  handleEdit,
  handleDelete,
}) => {
  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow className="bg-primary/5">
              <TableHead>Kode</TableHead>
              <TableHead>Nama</TableHead>
              <TableHead>Tipe</TableHead>
              <TableHead>Kapasitas</TableHead>
              <TableHead>Gedung</TableHead>
              <TableHead>Grup</TableHead>
              <TableHead className="text-right">Aksi</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center h-32">
                  <div className="flex items-center justify-center">
                    Loading...
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              ruangan.map((room) => (
                <TableRow key={room.kode_ruangan}>
                  <TableCell>{room.kode_ruangan}</TableCell>
                  <TableCell>{room.nama_ruang}</TableCell>
                  <TableCell>{room.tipe_ruangan}</TableCell>
                  <TableCell>{room.kapasitas}</TableCell>
                  <TableCell>{room.gedung}</TableCell>
                  <TableCell>{room.group_code}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleEdit(room)}
                    >
                      <Pencil className="h-4 w-4 text-blue-500" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => handleDelete(room.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* <div className="flex justify-between items-center mt-4">
        <Button onClick={() => setPage(page - 1)} disabled={page === 1}>
          Previous
        </Button>
        <span>
          Page {page} of {Math.ceil(total / pageSize)}
        </span>
        <Button
          onClick={() => setPage(page + 1)}
          disabled={page * pageSize >= total}
        >
          Next
        </Button>
      </div> */}
    </>
  );
};

export default RuanganTable;
