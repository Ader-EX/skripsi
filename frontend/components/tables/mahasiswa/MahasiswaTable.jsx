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
            <TableHead>NIM/NIP</TableHead>
            <TableHead>Nama</TableHead>
            <TableHead>Program Studi</TableHead>
            <TableHead>Semester</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mahasiswaList.map((mhs) => (
            <TableRow key={mhs.id}>
              <TableCell>{mhs.nim_nip || ""}</TableCell>
              <TableCell>{mhs.nama || ""}</TableCell>
              <TableCell>{mhs.program_studi_name || ""}</TableCell>
              <TableCell>{mhs.semester || 0}</TableCell>
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

      {/* Dialog for Viewing Details */}
      {selectedMahasiswa && (
        <Dialog
          open={selectedMahasiswa !== null}
          onOpenChange={() => setSelectedMahasiswa(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detail Mahasiswa</DialogTitle>
            </DialogHeader>
            <div className="space-y-2">
              <p>
                <strong>NIM/NIP:</strong> {selectedMahasiswa.nim_nip}
              </p>
              <p>
                <strong>Nama:</strong> {selectedMahasiswa.nama}
              </p>
              <p>
                <strong>Program Studi:</strong>{" "}
                {selectedMahasiswa.program_studi_name}
              </p>
              <p>
                <strong>Semester:</strong> {selectedMahasiswa.semester}
              </p>
              <p>
                <strong>SKS Diambil:</strong> {selectedMahasiswa.sks_diambil}
              </p>
              <p>
                <strong>Jenis Kelamin:</strong>{" "}
                {selectedMahasiswa.jenis_kelamin}
              </p>
              <p>
                <strong>Tempat Lahir:</strong> {selectedMahasiswa.kota_lahir}
              </p>
              <p>
                <strong>Tanggal Lahir:</strong> {selectedMahasiswa.tgl_lahir}
              </p>
              <p>
                <strong>Kewarganegaraan:</strong>{" "}
                {selectedMahasiswa.kewarganegaraan}
              </p>
            </div>
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
