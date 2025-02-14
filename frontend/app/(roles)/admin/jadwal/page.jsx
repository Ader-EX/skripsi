"use client";
import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import TimeTableView from "./TimeTableView";
import {
  Info,
  RefreshCcw,
  Settings,
  AlertTriangle,
  Search,
} from "lucide-react";
import toast from "react-hot-toast";
import debounce from "lodash.debounce";

const AdminJadwal = () => {
  const [timetableData, setTimetableData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isCheckingConflicts, setIsCheckingConflicts] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

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

  const handleGenerateSchedule = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/generate-schedule-sa/`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast.success("Schedule Generated Successfully", {
        description: "New timetable has been created using Simulated Annealing",
      });

      fetchTimetableData(searchQuery);
    } catch (err) {
      toast.error("Failed to Generate Schedule", {
        description: err.message,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleResetSchedule = async () => {
    setIsResetting(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/reset-schedule/`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      toast.success("Schedule Reset Successfully", {
        description: "Timetable has been reset to initial state",
      });

      fetchTimetableData(searchQuery);
    } catch (err) {
      toast.error("Failed to Reset Schedule", {
        description: err.message,
      });
    } finally {
      setIsResetting(false);
    }
  };

  const handleCheckConflicts = async () => {
    setIsCheckingConflicts(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/check-conflicts/`,
        { method: "GET" }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const conflictsData = await response.json();

      if (conflictsData.conflicts && conflictsData.conflicts.length > 0) {
        toast.warning("Conflicts Detected", {
          description: `Found ${conflictsData.conflicts.length} schedule conflicts`,
        });
      } else {
        toast.success("No Conflicts", {
          description: "No scheduling conflicts were found",
        });
      }

      // Refresh the timetable to show updated conflict status
      fetchTimetableData(searchQuery);
    } catch (err) {
      toast.error("Failed to Check Conflicts", {
        description: err.message,
      });
    } finally {
      setIsCheckingConflicts(false);
    }
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
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Timetable Management</h1>
          <div className="flex gap-4">
            <Button
              onClick={handleGenerateSchedule}
              disabled={isGenerating}
              className="flex items-center gap-2"
            >
              <Settings className={isGenerating ? "animate-spin" : ""} />
              {isGenerating ? "Generating..." : "Generate Timetable"}
            </Button>

            <Button
              onClick={handleResetSchedule}
              disabled={isResetting}
              variant="outline"
              className="flex items-center gap-2"
            >
              <RefreshCcw className={isResetting ? "animate-spin" : ""} />
              {isResetting ? "Resetting..." : "Reset Timetable"}
            </Button>

            <Button
              onClick={handleCheckConflicts}
              disabled={isCheckingConflicts}
              variant="destructive"
              className="flex items-center gap-2"
            >
              <AlertTriangle />
              {isCheckingConflicts ? "Checking..." : "Check Conflicts"}
            </Button>
          </div>
        </div>

        <div className="relative w-full max-w-sm mt-4">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search courses..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="pl-8"
          />
        </div>
      </div>

      <div className="flex-1 ">
        <TimeTableView
          schedules={timetableData.schedules || []}
          rooms={timetableData.rooms || []}
          timeSlots={timetableData.time_slots || []}
          filters={timetableData.filters || {}}
        />
      </div>
    </div>
  );
};

export default AdminJadwal;
