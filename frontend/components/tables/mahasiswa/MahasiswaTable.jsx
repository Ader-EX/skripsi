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
import { Eye, Pencil, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const MahasiswaTable = ({ mahasiswaList, onEdit, onDelete }) => {
  const [selectedMahasiswa, setSelectedMahasiswa] = useState(null);

  return (
    <div className="overflow-x-auto">
      <Table className="w-full">
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>ID</TableHead>
            <TableHead>Nama</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Program Studi</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mahasiswaList.map((mhs) => (
            <TableRow key={mhs.id}>
              <TableCell>{mhs.id}</TableCell>
              <TableCell>{mhs.user.fullname}</TableCell>
              <TableCell>{mhs.user.email}</TableCell>
              <TableCell>{mhs.program_studi_name}</TableCell>
              <TableCell className="text-right">
                <div className="flex gap-2 justify-end">
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => setSelectedMahasiswa(mhs)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onEdit(mhs)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onDelete(mhs.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Dialog for viewing details */}
      {selectedMahasiswa && (
        <Dialog
          open={selectedMahasiswa !== null}
          onOpenChange={() => setSelectedMahasiswa(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detail Mahasiswa</DialogTitle>
            </DialogHeader>
            <p>
              <strong>Nama:</strong> {selectedMahasiswa.user.fullname}
            </p>
            <p>
              <strong>Email:</strong> {selectedMahasiswa.user.email}
            </p>
            <p>
              <strong>Program Studi:</strong>{" "}
              {selectedMahasiswa.program_studi_name}
            </p>
            <div className="flex justify-end mt-4">
              <Button
                variant="outline"
                onClick={() => setSelectedMahasiswa(null)}
              >
                Tutup
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default MahasiswaTable;
