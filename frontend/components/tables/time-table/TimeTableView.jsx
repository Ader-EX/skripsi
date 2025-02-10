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

const TimeTableView = ({ scheduleList, onEdit, onDelete, loading }) => {
  const [selectedSchedule, setSelectedSchedule] = useState(null);

  const formatTime = (time) => {
    return new Date(`2024-01-01T${time}`).toLocaleTimeString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  if (loading) {
    return <div className="text-center py-4">Loading...</div>;
  }

  return (
    <div className="overflow-x-auto">
      <Table className="w-full">
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>Hari</TableHead>
            <TableHead>Mata Kuliah</TableHead>
            <TableHead>Kelas</TableHead>
            <TableHead>Dosen</TableHead>
            <TableHead>Waktu</TableHead>
            <TableHead>Ruangan</TableHead>
            <TableHead>Kapasitas</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scheduleList.map((schedule) => (
            <TableRow key={schedule.id}>
              <TableCell>{schedule.timeslots[0]?.day || ""}</TableCell>
              <TableCell>
                <div>
                  <div>{schedule.subject?.name}</div>
                  <div className="text-xs text-gray-500">
                    {schedule.subject?.code}
                  </div>
                </div>
              </TableCell>
              <TableCell>{schedule.class}</TableCell>
              <TableCell>
                {schedule.lecturers
                  ?.map((lecturer) => lecturer.name)
                  .join(", ")}
              </TableCell>
              <TableCell>
                {schedule.timeslots.length > 0 &&
                  `${schedule.timeslots[0].startTime} - ${
                    schedule.timeslots[schedule.timeslots.length - 1].endTime
                  }`}
              </TableCell>
              <TableCell>
                <div>
                  <div>{schedule.room?.code}</div>
                  <div className="text-xs text-gray-500">
                    Kapasitas: {schedule.room?.capacity}
                  </div>
                </div>
              </TableCell>
              <TableCell>
                {schedule.enrolled}/{schedule.capacity}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex gap-2 justify-end">
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => setSelectedSchedule(schedule)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onEdit(schedule)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => onDelete(schedule.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Detail Dialog */}
      {selectedSchedule && (
        <Dialog
          open={selectedSchedule !== null}
          onOpenChange={() => setSelectedSchedule(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Detail Jadwal</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="font-semibold">Mata Kuliah</p>
                  <p>{selectedSchedule.subject?.name}</p>
                  <p className="text-sm text-gray-500">
                    {selectedSchedule.subject?.code}
                  </p>
                </div>
                <div>
                  <p className="font-semibold">Kelas</p>
                  <p>{selectedSchedule.class}</p>
                </div>
                <div>
                  <p className="font-semibold">Dosen</p>
                  <p>
                    {selectedSchedule.lecturers
                      ?.map((lecturer) => lecturer.name)
                      .join(", ")}
                  </p>
                </div>
                <div>
                  <p className="font-semibold">Hari & Waktu</p>
                  {selectedSchedule.timeslots.map((slot, index) => (
                    <p key={index}>
                      {slot.day}: {slot.startTime} - {slot.endTime}
                    </p>
                  ))}
                </div>
                <div>
                  <p className="font-semibold">Ruangan</p>
                  <p>{selectedSchedule.room?.code}</p>
                  <p className="text-sm text-gray-500">
                    Kapasitas: {selectedSchedule.room?.capacity}
                  </p>
                </div>
                <div>
                  <p className="font-semibold">Kapasitas Kelas</p>
                  <p>
                    {selectedSchedule.enrolled}/{selectedSchedule.capacity}{" "}
                    mahasiswa
                  </p>
                </div>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <Button
                variant="outline"
                onClick={() => setSelectedSchedule(null)}
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

export default TimeTableView;
