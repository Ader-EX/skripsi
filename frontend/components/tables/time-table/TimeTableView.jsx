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
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_CHECK_CONFLICTS = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/check-conflicts`;
const API_RESOLVER_CONFLICTS = `${process.env.NEXT_PUBLIC_API_URL}/timetable/resolve-conflicts`;

const TimeTableView = ({ scheduleList, loading }) => {
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  const [showAutoResolveConfirm, setShowAutoResolveConfirm] = useState(false);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const router = useRouter();
  const token = Cookies.get("access_token");

  // Loading overlay controls from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/timetable/${confirmDelete}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
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
      // Activate the overlay with a custom message before fetching
      setOverlayText("Mengecek konflik jadwal...");
      setIsActive(true);
      const response = await fetch(API_CHECK_CONFLICTS, {
        headers: { Authorization: `Bearer ${token}` },
      });
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
      toast.error("Gagal mengecek konflik");
    } finally {
      setIsActive(false);
    }
  };

  const AutomateConflict = async () => {
    try {
      setOverlayText("Menyelesaikan konflik jadwal...");
      setIsActive(true);
      const response = await fetch(API_RESOLVER_CONFLICTS, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error("Gagal menyelesaikan bentrok.");
      const data = await response.json();
      toast.success("Konflik berhasil diubah");
      setTimeout(() => location.reload(), 2000);
    } catch (error) {
      console.error("Error resolving conflicts:", error);
      toast.error("Gagal menyelesaikan konflik");
    } finally {
      setIsActive(false);
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
          <RefreshCcw className="h-4 w-4 mr-2" />
          Cek Konflik
        </Button>
        <Button
          onClick={() => setShowAutoResolveConfirm(true)}
          variant="outline"
        >
          <BotIcon className="h-4 w-4 mr-2" />
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
            <TableHead>Program Studi</TableHead>
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
              <TableCell>
                {schedule.timeslots[0]?.day || "-"} -{" "}
                {schedule.timeslots.length > 0 &&
                  `${schedule.timeslots[0].startTime} - ${
                    schedule.timeslots[schedule.timeslots.length - 1].endTime
                  }`}
              </TableCell>
              <TableCell>{schedule.subject?.program_studi_name}</TableCell>
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
                  <Button size="icon" variant="outline">
                    <Link
                      href={`/admin/data-manajemen/edit?id=${schedule.id}`}
                      className="text-blue-500"
                    >
                      <Pencil />
                    </Link>
                  </Button>
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

      {/* Selected Schedule Details Dialog */}
      <Dialog
        open={!!selectedSchedule}
        onOpenChange={(open) => {
          if (!open) setSelectedSchedule(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Detail Jadwal</DialogTitle>
          </DialogHeader>
          {selectedSchedule && (
            <div className="space-y-4">
              <p>
                <strong>Mata Kuliah:</strong> {selectedSchedule.subject?.name} (
                {selectedSchedule.subject?.code})
              </p>
              <p>
                <strong>Kelas:</strong> {selectedSchedule.class}
              </p>
              <p>
                <strong>Dosen:</strong>{" "}
                {selectedSchedule.lecturers
                  ?.map((lecturer) => lecturer.name)
                  .join(", ")}
              </p>
              <p>
                <strong>Hari & Waktu:</strong>{" "}
                {selectedSchedule.timeslots[0]?.day}{" "}
                {selectedSchedule.timeslots.length > 0 &&
                  `${selectedSchedule.timeslots[0].startTime} - ${
                    selectedSchedule.timeslots[
                      selectedSchedule.timeslots.length - 1
                    ].endTime
                  }`}
              </p>
              <p>
                <strong>Ruangan:</strong> {selectedSchedule.room?.code}{" "}
                (Kapasitas: {selectedSchedule.room?.capacity})
              </p>
              <p>
                <strong>Jumlah Mahasiswa:</strong> {selectedSchedule.enrolled} /{" "}
                {selectedSchedule.capacity}
              </p>
              <p>
                <strong>Placeholder:</strong>
              </p>
              <pre className="bg-gray-100 p-2 rounded">
                {selectedSchedule.placeholder}
              </pre>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setSelectedSchedule(null)}>Tutup</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Conflict Resolution Dialog */}
      <Dialog open={showConflictDialog} onOpenChange={setShowConflictDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Konflik</DialogTitle>
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

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={confirmDelete !== null}
        onOpenChange={() => setConfirmDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Hapus Jadwal</DialogTitle>
          </DialogHeader>
          <p>
            Are you sure you want to delete this timetable entry? This action
            cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Auto-Resolve Confirmation Dialog */}
      <Dialog
        open={showAutoResolveConfirm}
        onOpenChange={setShowAutoResolveConfirm}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Konfirmasi Penyelesaian Otomatis</DialogTitle>
          </DialogHeader>
          <p className="mb-4 text-red-600">
            <span className="font-bold">Peringatan:</span> Menggunakan
            penyelesaian konflik otomatis kadang-kadang dapat menyebabkan
            masalah tambahan. Apakah Anda yakin ingin melanjutkan?
          </p>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowAutoResolveConfirm(false)}
            >
              Batal
            </Button>
            <Button
              onClick={() => {
                setShowAutoResolveConfirm(false);
                AutomateConflict();
              }}
            >
              Lanjutkan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TimeTableView;
