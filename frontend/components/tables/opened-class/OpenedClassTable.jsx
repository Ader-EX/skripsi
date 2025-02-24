import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Eye, Pencil, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useState } from "react";
import { useSearchParams, usePathname } from "next/navigation";
const getTipeMKLabel = (tipe) => {
  const mapping = {
    S: "Spesial",
    P: "Praktikum",
    T: "Teori",
  };
  return mapping[tipe] || "Unknown";
};

export const OpenedClassTable = ({ classList, onDelete, loading }) => {
  const router = useRouter();
  const [selectedClass, setSelectedClass] = useState(null);
  const searchParams = useSearchParams(); // ✅ Get current searchParams
  const pathname = usePathname(); // ✅ Get current pathname

  if (loading) {
    return <div className="text-center py-4">Loading...</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-primary/5">
            <th className="p-2 text-left">Kode</th>
            <th className="p-2 text-left">Mata Kuliah</th>
            <th className="p-2 text-left">Program Studi</th>
            <th className="p-2 text-left">Tipe</th>
            <th className="p-2 text-left">Kelas</th>
            <th className="p-2 text-left">Dosen</th>
            <th className="p-2 text-left">Kapasitas</th>
            <th className="p-2 text-left">SKS</th>
            <th className="p-2 text-right">Aksi</th>
          </tr>
        </thead>
        <tbody>
          {classList.map((classItem) => (
            <tr key={classItem.id} className="border-b">
              <td className="p-2">{classItem.mata_kuliah.kode}</td>
              <td className="p-2">{classItem.mata_kuliah.nama}</td>
              <td className="p-2">{classItem.mata_kuliah.program_studi}</td>
              <td className="p-2">
                {getTipeMKLabel(classItem.mata_kuliah.tipe_mk)}
              </td>
              <td className="p-2">{classItem.kelas}</td>
              <td className="p-2">
                {classItem.dosens.map((dosen) => dosen.fullname).join(", ")}
              </td>
              <td className="p-2">{classItem.kapasitas}</td>
              <td className="p-2">{classItem.mata_kuliah.sks}</td>
              <td className="p-2 text-right">
                <div className="flex gap-2 justify-end">
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => setSelectedClass(classItem)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => {
                      const newParams = new URLSearchParams(searchParams);
                      newParams.set("id", classItem.id); // ✅ Set opened_class_id in searchParams
                      router.push(
                        `${pathname}/edit-opened?${newParams.toString()}`
                      ); // ✅ Updates URL without full reload
                    }}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onDelete(classItem.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedClass && (
        <Dialog
          open={selectedClass !== null}
          onOpenChange={() => setSelectedClass(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detail Kelas</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="font-semibold">Mata Kuliah</p>
                  <p>{selectedClass.mata_kuliah.nama}</p>
                  <p className="text-sm text-gray-500">
                    {selectedClass.mata_kuliah.kode}
                  </p>
                </div>
                <div>
                  <p className="font-semibold">Tipe</p>
                  <p>{getTipeMKLabel(selectedClass.mata_kuliah.tipe_mk)}</p>
                </div>
                <div>
                  <p className="font-semibold">Kelas</p>
                  <p>{selectedClass.kelas}</p>
                </div>
                <div>
                  <p className="font-semibold">Dosen</p>
                  <p>
                    {selectedClass.dosens
                      .map((dosen) => dosen.fullname)
                      .join(", ")}
                  </p>
                </div>
                <div>
                  <p className="font-semibold">SKS</p>
                  <p>{selectedClass.mata_kuliah.sks}</p>
                </div>
                <div>
                  <p className="font-semibold">Semester</p>
                  <p>{selectedClass.mata_kuliah.semester}</p>
                </div>
                <div>
                  <p className="font-semibold">Kapasitas</p>
                  <p>{selectedClass.kapasitas} mahasiswa</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button variant="outline" onClick={() => setSelectedClass(null)}>
                Tutup
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};
