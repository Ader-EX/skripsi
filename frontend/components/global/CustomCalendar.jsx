"use client";
import React, { useState } from "react";
import { Select } from "@/components/ui/select";

const DUMMY_DATA = [
  {
    id: 1,
    subject: "Statistika dan Probabilitas - A",
    room: "DS-301",
    lecturer: "Dr. John Doe",
    day: "Monday",
    startTime: "07:00",
    endTime: "08:40",
  },
  {
    id: 2,
    subject: "Praktikum Data Mining",
    room: "KH-401",
    lecturer: "Dr. Jane Smith",
    day: "Monday",
    startTime: "07:00",
    endTime: "09:30",
  },
];

const DAYS = [
  "All Days",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
];

const TIME_SLOTS = [
  "07:00-07:50",
  "07:50-08:40",
  "08:40-09:30",
  "09:30-10:20",
  "10:20-11:10",
  "11:10-12:00",
];

const ROOMS = ["DS-301", "KH-401", "KH-202", "KH-201"];

const CustomCalendar = () => {
  const [selectedDay, setSelectedDay] = useState("All Days");

  const filteredData = DUMMY_DATA.filter(
    (item) => selectedDay === "All Days" || item.day === selectedDay
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">Jadwal Tetap</h1>
        <h2 className="text-gray-600 mb-4">Tahun Ajaran 2024/2025</h2>

        <div className="flex justify-between items-center mb-4">
          <select
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value)}
            className="border border-gray-300 rounded-md px-4 py-2 w-48"
          >
            {DAYS.map((day) => (
              <option key={day} value={day}>
                {day}
              </option>
            ))}
          </select>

          <button className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors">
            Export to Excel
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse">
          <thead>
            <tr className="bg-gray-50">
              <th className="border px-4 py-2 text-left">Day</th>
              <th className="border px-4 py-2 text-left">Time</th>
              {ROOMS.map((room) => (
                <th key={room} className="border px-4 py-2 text-left">
                  {room}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {TIME_SLOTS.map((timeSlot, index) => (
              <tr
                key={timeSlot}
                className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}
              >
                <td className="border px-4 py-2">
                  {index === 0 ? selectedDay : ""}
                </td>
                <td className="border px-4 py-2">{timeSlot}</td>
                {ROOMS.map((room) => {
                  const classSession = filteredData.find(
                    (item) =>
                      item.room === room && timeSlot.startsWith(item.startTime)
                  );

                  return (
                    <td key={room} className="border px-4 py-2">
                      {classSession && (
                        <div className="bg-gray-200 p-2 rounded">
                          <div className="font-medium">
                            {classSession.subject}
                          </div>
                          <div className="text-sm text-gray-600">
                            {classSession.lecturer}
                          </div>
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CustomCalendar;
