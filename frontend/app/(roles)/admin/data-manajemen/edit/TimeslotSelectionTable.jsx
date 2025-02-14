"use client";
import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";

const TimeslotSelectionTable = ({
  availableTimeslots,
  selectedTimeslots,
  onTimeslotToggle,
  timetableTimeslots, // Pass in previously selected timeslots from timetable/{id}
}) => {
  // Group timeslots by start_time so each row represents a unique time slot
  const groupedByTime = availableTimeslots.reduce((acc, timeslot) => {
    if (!acc[timeslot.start_time]) acc[timeslot.start_time] = [];
    acc[timeslot.start_time].push(timeslot);
    return acc;
  }, {});

  // Extract unique days for columns (X-axis)
  const uniqueDays = [...new Set(availableTimeslots.map((slot) => slot.day))];

  return (
    <div className="mt-6">
      <h2 className="text-lg font-bold mb-3">Pilih Timeslot</h2>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[150px]">Waktu</TableHead>
            {uniqueDays.map((day) => (
              <TableHead key={day} className="text-center">
                {day}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.entries(groupedByTime).map(([startTime, slots]) => (
            <TableRow key={startTime}>
              <TableCell className="font-medium">
                {startTime} - {slots[0].end_time}
              </TableCell>
              {uniqueDays.map((day) => {
                const timeslot = slots.find((slot) => slot.day === day);
                return (
                  <TableCell
                    key={`${day}-${startTime}`}
                    className="text-center"
                  >
                    {timeslot ? (
                      <Checkbox
                        checked={selectedTimeslots.includes(
                          timeslot.timeslot_id
                        )}
                        onCheckedChange={() =>
                          onTimeslotToggle(timeslot.timeslot_id)
                        }
                        disabled={
                          timeslot.status === "Busy" &&
                          !timetableTimeslots.includes(timeslot.timeslot_id) // Enable if previously selected
                        }
                      />
                    ) : (
                      "-"
                    )}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default TimeslotSelectionTable;
