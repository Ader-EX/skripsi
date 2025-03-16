"use client";
import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import TimeTableView from "./TimeTableView";
import { RefreshCcw, Settings, AlertTriangle, Search } from "lucide-react";
import toast from "react-hot-toast";
import debounce from "lodash.debounce";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { LoadingOverlay } from "@/components/global/CustomLoadingOverlay";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";
import Link from "next/link";

const AdminJadwal = () => {
  const [timetableData, setTimetableData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isCheckingConflicts, setIsCheckingConflicts] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [conflicts, setConflicts] = useState([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const [selectedDay, setSelectedDay] = useState("Senin");
  // Added state for reset confirmation dialog
  const [showResetConfirmDialog, setShowResetConfirmDialog] = useState(false);

  // Use 0-based indexing so that "Senin" is 0, matching your API data.
  const dayMapping = {
    Senin: 0,
    Selasa: 1,
    Rabu: 2,
    Kamis: 3,
    Jumat: 4,
    Sabtu: 5,
  };

  const router = useRouter();
  const token = Cookies.get("access_token");
  const { setIsActive, setOverlayText } = useLoadingOverlay();
  const [isAlgorithmDialogOpen, setIsAlgorithmDialogOpen] = useState(false);

  const handleCloseAlgorithmDialog = () => {
    setIsAlgorithmDialogOpen(false);
  };

  const fetchTimetableData = async (search = "", selectedDay = "Senin") => {
    try {
      setLoading(true);
      const url = new URL(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/timetable-view/`
      );
      if (search) {
        url.searchParams.append("search", search);
      }
      // Append day_index from our 0-based mapping
      const dayIndex = dayMapping[selectedDay];
      url.searchParams.append("day_index", dayIndex);

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTimetableData(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
      toast.error("Failed to load timetable", {
        description: err.message,
      });
    }
  };

  // Debounce search input
  const debouncedSearch = debounce((query) => {
    fetchTimetableData(query, selectedDay);
  }, 500);

  useEffect(() => {
    fetchTimetableData();
  }, []);

  // Re-fetch data when selectedDay changes
  useEffect(() => {
    fetchTimetableData(searchQuery, selectedDay);
  }, [selectedDay]);

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

  const handleSearchSubmit = () => {
    fetchTimetableData(searchQuery, selectedDay);
  };

  // Modified to show confirmation dialog first
  const handleResetButtonClick = () => {
    setShowResetConfirmDialog(true);
  };

  const handleResetSchedule = async () => {
    setIsResetting(true);
    setShowResetConfirmDialog(false);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/reset-schedule/`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      await response.json();
      toast.success("Schedule Reset Successfully", {
        description: "Timetable has been reset to initial state",
      });
      fetchTimetableData(searchQuery, selectedDay);
    } catch (err) {
      toast.error("Failed to Reset Schedule", {
        description: err.message,
      });
    } finally {
      setIsResetting(false);
    }
  };

  const handleGenerateHybrid = async () => {
    setIsGenerating(true);
    setOverlayText(
      "Membuat Jadwal Otomatis, silahkan tunggu dan jangan refresh halaman ini sampai selesai..."
    );
    setIsActive(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/hybrid-router/generate-schedule-hybrid`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      await response.json();
      setIsGenerating(false);
      toast.success("Schedule Generated Successfully (Hybrid)", {
        description: "New timetable has been created",
      });
      router.refresh();
      fetchTimetableData(searchQuery);
    } catch (err) {
      toast.error("Failed to Generate Schedule", {
        description: err.message,
      });
    } finally {
      setIsGenerating(false);
      setIsActive(false);
      handleCloseAlgorithmDialog();
    }
  };

  // (Other generate/check functions remain unchanged)

  if (loading) {
    return (
      <div className="flex-1">
        <div className="flex items-center justify-center w-full h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <span className="ml-2">Loading timetable data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-8">
        <Card className="p-8">
          <div className="text-red-500 text-center">
            Error loading timetable: {error}
          </div>
        </Card>
      </div>
    );
  }

  if (!timetableData) {
    return (
      <div className="ml-10 p-8">
        <Card className="p-8">
          <div className="text-center">No timetable data available</div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full">
      <div className="flex flex-col h-screen w-full">
        <div className="flex-none p-4 mb-4">
          <div className="flex justify-between items-start mt-4">
            <h1 className="text-2xl font-bold">Timetable Management</h1>
            <div className="relative w-full flex flex-col sm:flex-row max-w-sm mb-4">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search courses..."
                value={searchQuery}
                onChange={handleSearchChange}
                className="pl-8 flex-1"
              />
              <Button onClick={handleSearchSubmit} className="ml-2">
                <Search className="h-4 w-4 text-muted-foreground" />
              </Button>
            </div>
          </div>

          <div className="flex w-full flex-col sm:flex-row gap-4">
            <Button
              onClick={handleGenerateHybrid}
              disabled={isGenerating}
              className="flex items-center gap-2"
            >
              <Settings className={isGenerating ? "animate-spin" : ""} />
              {isGenerating ? "Generating..." : "Generate Timetable"}
            </Button>

            <div className="flex w-full flex-col sm:flex-row gap-x-4 justify-end">
              <Button
                onClick={handleResetButtonClick}
                disabled={isResetting}
                variant="outline"
                className="flex items-center gap-2 bg-red-500 text-white"
              >
                <RefreshCcw className={isResetting ? "animate-spin" : ""} />
                {isResetting ? "Mengatur Ulang..." : "Reset Jadwal"}
              </Button>

              <Button
                variant="outline"
                className="flex items-center gap-2 bg-yellow-400"
                onClick={() => {
                  router.push("/admin/data-manajemen");
                }}
              >
                <AlertTriangle />
                {isCheckingConflicts ? "Checking..." : "Check Conflicts"}
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1">
          <TimeTableView
            schedules={timetableData.schedules || []}
            rooms={timetableData.rooms || []}
            timeSlots={timetableData.time_slots || []}
            filters={timetableData.filters || {}}
            selectedDay={selectedDay}
            onDayChange={setSelectedDay}
            role="admin"
          />
        </div>

        {/* Reset Confirmation Dialog in Bahasa Indonesia */}
        <Dialog
          open={showResetConfirmDialog}
          onOpenChange={setShowResetConfirmDialog}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Konfirmasi Reset Jadwal</DialogTitle>
              <DialogDescription className="pt-2">
                Apakah Anda yakin ingin mengatur ulang seluruh jadwal? Tindakan
                ini akan menghapus semua jadwal yang telah dibuat.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="flex flex-col sm:flex-row gap-2 sm:justify-end">
              <Button
                variant="outline"
                onClick={() => setShowResetConfirmDialog(false)}
              >
                Batal
              </Button>
              <Button
                onClick={handleResetSchedule}
                className="bg-red-500 hover:bg-red-600 text-white"
                disabled={isResetting}
              >
                {isResetting ? "Sedang Diproses..." : "Ya, Reset Jadwal"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showConflictDialog} onOpenChange={setShowConflictDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Schedule Conflicts</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {conflicts.length > 0 ? (
                <ul className="list-disc pl-5 text-red-500">
                  {conflicts.map((conflict, index) => (
                    <li key={index}>
                      {conflict.type} - {conflict.reason}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No conflicts found.</p>
              )}
            </div>
            <DialogFooter>
              <Button
                onClick={() => router.push("/admin/data-manajemen")}
                className="bg-red-500 hover:bg-red-600"
              >
                Resolve Conflicts
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default AdminJadwal;
