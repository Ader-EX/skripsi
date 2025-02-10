"use client";
import React, { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import TimeTableView from "./TimeTableView";

const AdminJadwal = () => {
  const [timetableData, setTimetableData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTimetableData = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/algorithm/timetable-view/"
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setTimetableData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchTimetableData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 p-8">
        <Card className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            <span className="ml-2">Loading timetable data...</span>
          </div>
        </Card>
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
    <div className=" flex flex-col h-screen">
      <div className="flex-none p-8">
        <h1 className="text-2xl font-bold ">Timetable Management</h1>
      </div>
      <div className="flex-1 px-8 pb-8 overflow-hidden">
        <TimeTableView
          schedules={timetableData.schedules}
          rooms={timetableData.rooms}
          timeSlots={timetableData.time_slots}
        />
      </div>
    </div>
  );
};

export default AdminJadwal;
