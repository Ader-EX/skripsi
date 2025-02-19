"use client";
import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  Info,
  RefreshCcw,
  Settings,
  AlertTriangle,
  Search,
} from "lucide-react";
import toast from "react-hot-toast";
import debounce from "lodash.debounce";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useRouter } from "next/navigation";
import TimeTableView from "../../admin/jadwal/TimeTableView";

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
  const router = useRouter();

  const [isAlgorithmDialogOpen, setIsAlgorithmDialogOpen] = useState(false);

  const handleOpenAlgorithmDialog = () => {
    setIsAlgorithmDialogOpen(true);
  };

  const handleCloseAlgorithmDialog = () => {
    setIsAlgorithmDialogOpen(false);
  };

  const API_CHECK_CONFLICTS = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/check-conflicts`;

  const handleGenerateSimulatedAnnealing = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/sa-router/generate-schedule-sa/`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      toast.success("Schedule Generated Successfully (Simulated Annealing)", {
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
      handleCloseAlgorithmDialog();
    }
  };

  // Handler untuk Genetic Algorithm
  const handleGenerateGeneticAlgorithm = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/ga-router/generate-schedule-ga/`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast.success("Schedule Generated Successfully (Genetic Algorithm)", {
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
      handleCloseAlgorithmDialog(); // Tutup dialog setelah selesai
    }
  };

  const fetchTimetableData = async (search = "") => {
    try {
      const url = new URL(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/timetable-view/`
      );
      if (search) {
        url.searchParams.append("search", search);
      }

      const response = await fetch(url);
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

  // Debounced search function
  const debouncedSearch = debounce((query) => {
    fetchTimetableData(query);
  }, 500);

  useEffect(() => {
    fetchTimetableData();
  }, []);

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    debouncedSearch(query);
  };

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
    <div className="flex flex-col h-screen w-full">
      <div className="flex-none p-4 mb-4">
        <div className="flex justify-between  items-start mt-4">
          <h1 className="text-2xl font-bold ">Timetable Management</h1>
          <div className="relative w-full flex flex-col sm:flex-row max-w-sm mb-4 ">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 flex-1"
            />
            <Button
              onClick={() => fetchTimetableData(searchQuery)}
              className="ml-2"
            >
              <Search className="h-4 w-4 text-muted-foreground" />
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 ">
        <TimeTableView
          schedules={timetableData.schedules || []}
          rooms={timetableData.rooms || []}
          timeSlots={timetableData.time_slots || []}
          filters={timetableData.filters || {}}
          role="dosen"
        />
      </div>
    </div>
  );
};

export default AdminJadwal;
