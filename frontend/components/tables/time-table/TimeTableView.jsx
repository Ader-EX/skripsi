"use client";
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
  Eye,
  Pencil,
  Trash2,
  AlertCircle,
  CheckCircle,
  RefreshCcw,
  BotIcon,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import Link from "next/link";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const API_CHECK_CONFLICTS = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/check-conflicts`;
const API_RESOLVER_CONFLICTS = `${process.env.NEXT_PUBLIC_API_URL}/timetable/resolve-conflicts`;

const TimeTableView = ({ scheduleList, loading }) => {
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const router = useRouter();

  const handleDelete = async () => {
    if (!confirmDelete) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/timetable/${confirmDelete}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) throw new Error("Failed to delete timetable");

      toast.success("Jadwal berhasil dihapus");
      location.reload();
    } catch (error) {
      console.error("Error deleting timetable:", error);
      toast.error("Gagal menghapus jadwal");
    } finally {
      setConfirmDelete(null);
    }
  };

  const fetchConflicts = async () => {
    try {
      const response = await fetch(API_CHECK_CONFLICTS);
      if (!response.ok) throw new Error("Gagal mengecek bentrok.");

      const data = await response.json();
      if (data.total_conflicts > 0) {
        toast.error("Bentrok Ditemukan di jadwal");
        setTimeout(() => location.reload(), 2000);
      } else {
        toast.success("Tidak ada bentrok dalam jadwal.");
        setTimeout(() => location.reload(), 2000);
      }
    } catch (error) {
      console.error("Error checking conflicts:", error);
    }
  };

  const AutomateConflict = async () => {
    try {
      const response = await fetch(API_RESOLVER_CONFLICTS, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) throw new Error("Gagal menyelesaikan bentrok.");

      const data = await response.json();

      toast.success("Konflik berhasil diubah");
      setTimeout(() => location.reload(), 2000);
    } catch (error) {
      console.error("Error checking conflicts:", error);
    }
  };

  return (
    <div className="overflow-x-auto">
      <div className="flex flex-col sm:flex-row justify-end mb-4 gap-x-4">
        <Button
          onClick={fetchConflicts}
          variant="outline"
          className="bg-blue-500 text-white"
        >
          <RefreshCcw className="h-4 w-4 mr-2 " />
          Cek Konflik
        </Button>
        <Button onClick={AutomateConflict} variant="outline">
          <BotIcon className="h-4 w-4 mr-2 " />
          Selesaikan Konflik Otomatis
        </Button>
      </div>

      <Table className="w-full">
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>Mata Kuliah</TableHead>
            <TableHead>Kelas</TableHead>
            <TableHead>Dosen</TableHead>
            <TableHead>Hari</TableHead>
            <TableHead>Waktu</TableHead>
            <TableHead>Ruangan</TableHead>
            <TableHead>Kapasitas</TableHead>
            <TableHead>Bentrok</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {scheduleList.map((schedule) => (
            <TableRow key={schedule.id}>
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
              <TableCell>{schedule.timeslots[0]?.day || "-"}</TableCell>
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
                {schedule.enrolled || "0"}/{schedule.capacity}
              </TableCell>
              {/* ✅ Conflict Status Column with Tooltip */}
              <TableCell className="text-center">
                <Tooltip>
                  <TooltipTrigger>
                    {schedule.is_conflicted === false ||
                    schedule.is_conflicted === 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : schedule.is_conflicted === true ||
                      schedule.is_conflicted === 1 ? (
                      schedule.reason ? (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-yellow-500" />
                      )
                    ) : (
                      <AlertCircle className="h-5 w-5 text-gray-500" />
                    )}
                  </TooltipTrigger>

                  <TooltipContent>
                    {schedule.is_conflicted === false ||
                    schedule.is_conflicted === 0
                      ? "Jadwal tidak bentrok"
                      : schedule.is_conflicted === true ||
                        schedule.is_conflicted === 1
                      ? schedule.reason || "Perlu cek konflik terlebih dahulu"
                      : "Jadwal ini bentrok dengan jadwal lain"}
                  </TooltipContent>
                </Tooltip>
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

                  {/* Edit Button */}
                  <Button size="icon" variant="outline">
                    <Link
                      href={`/admin/data-manajemen/edit?id=${schedule.id}`}
                      className="text-blue-500"
                    >
                      <Pencil />
                    </Link>
                  </Button>

                  {/* Delete Button with Confirmation */}
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => setConfirmDelete(schedule.id)}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* 🛑 Conflict Dialog */}
      <Dialog open={showConflictDialog} onOpenChange={setShowConflictDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konflik Jadwal Ditemukan</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {conflicts.length > 0 ? (
              <div className="overflow-y-auto max-h-64">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Jenis Konflik</TableHead>
                      <TableHead>Mata Kuliah</TableHead>
                      <TableHead>Dosen</TableHead>
                      <TableHead>Ruangan</TableHead>
                      <TableHead>Waktu</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conflicts.map((conflict, index) => (
                      <TableRow key={index}>
                        <TableCell>{conflict.type}</TableCell>
                        <TableCell>{conflict.opened_class_id}</TableCell>
                        <TableCell>{conflict.dosen_id || "-"}</TableCell>
                        <TableCell>{conflict.room_id || "-"}</TableCell>
                        <TableCell>{conflict.timeslot_id}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <p>Tidak ada konflik ditemukan.</p>
            )}
          </div>
          <DialogFooter>
            <Button
              onClick={() => router.push("/admin/data-manajemen")}
              className="bg-red-500 hover:bg-red-600"
            >
              🔧 Resolve Conflicts
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={confirmDelete !== null}
        onOpenChange={() => setConfirmDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Hapus Jadwal</DialogTitle>
          </DialogHeader>
          <p>
            Apakah Anda yakin ingin menghapus jadwal ini? Data mahasiswa terkait
            juga akan dihapus.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(null)}>
              Batal
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Hapus
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TimeTableView;
