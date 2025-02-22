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
import { Trash2 } from "lucide-react";

const formatSchedule = (schedule) => {
  if (!schedule) return "-";
  return schedule.replace("DayEnum.", "");
};

const DosenTimetableManagementTable = ({ timetableList, onDelete }) => {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>Kode MK</TableHead>
            <TableHead>Mata Kuliah</TableHead>
            <TableHead>SKS</TableHead>
            <TableHead>Kelas</TableHead>
            <TableHead>Dosen</TableHead>
            <TableHead>Ruangan</TableHead>
            <TableHead>Jadwal</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {timetableList.map((subject) => (
            <TableRow key={subject.timetable_id}>
              <TableCell>{subject.kodemk}</TableCell>
              <TableCell>{subject.matakuliah}</TableCell>
              <TableCell>{subject.sks}</TableCell>
              <TableCell>{subject.kelas}</TableCell>
              <TableCell>{subject.dosen}</TableCell>
              <TableCell>{subject.ruangan}</TableCell>
              <TableCell>{formatSchedule(subject.schedule)}</TableCell>
              <TableCell className="text-right">
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => onDelete(subject.timetable_id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default DosenTimetableManagementTable;
