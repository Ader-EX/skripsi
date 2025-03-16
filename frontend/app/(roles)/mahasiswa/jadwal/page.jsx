"use client";
import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import toast from "react-hot-toast";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import TimeTableView from "../../admin/jadwal/TimeTableView";
import Cookies from "js-cookie";

const MahasiswaJadwal = () => {
  const [timetableData, setTimetableData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [conflicts, setConflicts] = useState([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const [selectedDay, setSelectedDay] = useState("Senin");
  const dayMapping = {
    Senin: 0,
    Selasa: 1,
    Rabu: 2,
    Kamis: 3,
    Jumat: 4,
    Sabtu: 5,
  };

  const token = Cookies.get("access_token");

  const fetchTimetableData = async (search = "", selectedDay = "Senin") => {
    try {
      setLoading(true);
      const url = new URL(
        `${process.env.NEXT_PUBLIC_API_URL}/algorithm/timetable-view/`
      );

      if (search) {
        url.searchParams.append("search", search);
      }

      // Get the index for the selected day
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

  useEffect(() => {
    fetchTimetableData(searchQuery, selectedDay);
  }, [selectedDay]);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  // FIXED: Use the current selectedDay instead of a hardcoded "1"
  const handleSearchSubmit = () => {
    fetchTimetableData(searchQuery, selectedDay);
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
        <div className="flex justify-between items-end">
          <h1 className="text-2xl font-bold">Timetable Management</h1>
          <div className="relative w-full max-w-sm mt-4 flex">
            <Input
              placeholder="Search courses..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-8"
            />
            <Button onClick={handleSearchSubmit} className="ml-2">
              <Search className="h-4 w-4 mr-1" /> Search
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1">
        <TimeTableView
          role="mahasiswa"
          schedules={timetableData.schedules || []}
          rooms={timetableData.rooms || []}
          timeSlots={timetableData.time_slots || []}
          filters={timetableData.filters || {}}
          selectedDay={selectedDay}
          onDayChange={setSelectedDay}
        />
      </div>

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
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MahasiswaJadwal;
