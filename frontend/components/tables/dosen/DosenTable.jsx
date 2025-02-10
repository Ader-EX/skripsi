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
import { format } from "date-fns";

const DosenTable = ({ dosenList, onEdit, onDelete }) => {
  const [selectedDosen, setSelectedDosen] = useState(null);

  return (
    <div className="overflow-x-auto">
      <Table className="w-full">
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>ID</TableHead>
            <TableHead>Nama</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>NIDN</TableHead>
            <TableHead>NIP</TableHead>
            <TableHead>Jabatan</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {dosenList.map((dosen) => (
            <TableRow key={dosen.id}>
              <TableCell>{dosen.id}</TableCell>
              <TableCell>{dosen.user.fullname}</TableCell>
              <TableCell>{dosen.user.email}</TableCell>
              <TableCell>{dosen.nidn || "-"}</TableCell>
              <TableCell>{dosen.nip || "-"}</TableCell>
              <TableCell>{dosen.jabatan || "-"}</TableCell>
              <TableCell className="text-right">
                <div className="flex gap-2 justify-end">
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => setSelectedDosen(dosen)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onEdit(dosen)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onDelete(dosen.id)}
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
      {selectedDosen && (
        <Dialog
          open={selectedDosen !== null}
          onOpenChange={() => setSelectedDosen(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detail Dosen</DialogTitle>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="font-semibold">Nama:</p>
                <p>{selectedDosen.user.fullname}</p>
              </div>
              <div>
                <p className="font-semibold">Email:</p>
                <p>{selectedDosen.user.email}</p>
              </div>
              <div>
                <p className="font-semibold">NIDN:</p>
                <p>{selectedDosen.nidn || "-"}</p>
              </div>
              <div>
                <p className="font-semibold">NIP:</p>
                <p>{selectedDosen.nip || "-"}</p>
              </div>
              <div>
                <p className="font-semibold">Nomor KTP:</p>
                <p>{selectedDosen.nomor_ktp || "-"}</p>
              </div>
              <div>
                <p className="font-semibold">Tanggal Lahir:</p>
                <p>
                  {selectedDosen.tanggal_lahir
                    ? format(
                        new Date(selectedDosen.tanggal_lahir),
                        "dd/MM/yyyy"
                      )
                    : "-"}
                </p>
              </div>
              <div>
                <p className="font-semibold">Jabatan:</p>
                <p>{selectedDosen.jabatan || "-"}</p>
              </div>
              <div>
                <p className="font-semibold">Title:</p>
                <p>
                  {[selectedDosen.title_depan, selectedDosen.title_belakang]
                    .filter(Boolean)
                    .join(" ") || "-"}
                </p>
              </div>
              <div>
                <p className="font-semibold">Status:</p>
                <p>
                  {[
                    selectedDosen.is_sekdos ? "Sekretaris Dosen" : "",
                    selectedDosen.is_dosen_kb ? "Dosen KB" : "",
                  ]
                    .filter(Boolean)
                    .join(", ") || "-"}
                </p>
              </div>
              <div>
                <p className="font-semibold">Izin Mengajar:</p>
                <p>{selectedDosen.ijin_mengajar ? "Ya" : "Tidak"}</p>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button variant="outline" onClick={() => setSelectedDosen(null)}>
                Tutup
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default DosenTable;
