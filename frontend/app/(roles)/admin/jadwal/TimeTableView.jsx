"use client";
import React, { useState, useMemo, useEffect } from "react";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Pencil } from "lucide-react";

const TimeTableView = ({
  schedules,
  rooms,
  timeSlots,
  filters,
  role = "admin",
}) => {
  const [DAYS, setDAYS] = useState(filters?.available_days || ["Senin"]);
  const [selectedDay, setSelectedDay] = useState(DAYS[0] || "Senin");
  const [selectedBuilding, setSelectedBuilding] = useState("all");
  const [selectedConflict, setSelectedConflict] = useState(null);
  console.log(schedules);

  const handleConflictClick = (schedule) => {
    if (schedule.is_conflicted && schedule.reason) {
      setSelectedConflict(schedule);
    }
  };

  const getConflictClass = (schedule) => {
    if (!schedule.is_conflicted) return "bg-green-100";
    if (schedule.is_conflicted && !schedule.reason) return "bg-yellow-100";
    return "bg-red-100";
  };

  const renderConflictModal = () => {
    if (!selectedConflict) return null;

    return (
      <Dialog
        open={selectedConflict !== null}
        onOpenChange={() => setSelectedConflict(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Conflict Details</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-red-600 font-semibold">
              {selectedConflict.reason}
            </p>
            <p>
              Severity:{" "}
              <strong>{selectedConflict.severity || "Unknown"}</strong>
            </p>
            <p>Room: {selectedConflict.room_id}</p>
            <p>Timeslot: {selectedConflict.timeslot_id}</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedConflict(null)}>
              Close
            </Button>
            <Button
              className="bg-red-500 hover:bg-red-600"
              onClick={() => (window.location.href = "/admin/data-manajemen")}
            >
              Resolve Conflict
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  };

  useEffect(() => {
    if (filters?.available_days) {
      setDAYS(filters.available_days);
      setSelectedDay(filters.available_days[0] || "Senin");
    }
  }, [filters]);

  const uniqueTimeSlots = useMemo(() => {
    return timeSlots
      .filter((slot) => slot.day === selectedDay)
      .filter(
        (slot, index, self) =>
          index ===
          self.findIndex(
            (s) =>
              s.start_time === slot.start_time && s.end_time === slot.end_time
          )
      )
      .sort((a, b) => a.start_time.localeCompare(b.start_time));
  }, [timeSlots, selectedDay]);

  const roomsByBuilding = useMemo(() => {
    const buildings = rooms.reduce((acc, room) => {
      if (!acc[room.building]) {
        acc[room.building] = [];
      }
      acc[room.building].push(room);
      return acc;
    }, {});

    if (selectedBuilding !== "all") {
      return {
        [selectedBuilding]: buildings[selectedBuilding],
      };
    }
    return buildings;
  }, [rooms, selectedBuilding]);

  const buildings = useMemo(() => {
    return [...new Set(rooms.map((room) => room.building))];
  }, [rooms]);

  const getScheduleForSlot = (timeSlot, roomId) => {
    return schedules.filter((schedule) => {
      if (schedule.room_id !== roomId) return false;
      return schedule.time_slots.some((ts) => ts.id === timeSlot.id);
    });
  };

  const renderScheduleCard = (scheduleList, timeSlot, roomId) => {
    if (!scheduleList.length) return null;

    // If there's more than 1 schedule in the cell, treat it as a multi-schedule conflict => Red
    if (scheduleList.length > 1) {
      return (
        <div
          className="h-full w-full p-2 flex flex-row gap-2 bg-red-100"
          style={{ whiteSpace: "nowrap", overflow: "hidden" }}
        >
          {scheduleList.map((schedule) => renderSingleSchedule(schedule))}
        </div>
      );
    }

    // If exactly one schedule, check its conflict status
    const schedule = scheduleList[0];
    let containerClass = "bg-green-100"; // default = no conflict

    if (schedule.is_conflicted) {
      if (schedule.reason) {
        // Conflict with reason => Red
        containerClass = "bg-red-100";
      } else {
        // Conflict without reason => Yellow
        containerClass = "bg-yellow-100";
      }
    }

    return (
      <div
        className={`h-full w-full p-2 flex flex-row gap-2 ${containerClass}`}
        style={{ whiteSpace: "nowrap", overflow: "hidden" }}
      >
        {renderSingleSchedule(schedule)}
      </div>
    );
  };

  // Factor out the rendering of a single schedule into a helper function
  function renderSingleSchedule(schedule) {
    return (
      <TooltipProvider key={schedule.id}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className="flex-1 p-2 rounded cursor-pointer overflow-hidden"
              style={{ minWidth: 0 }}
              onClick={() => handleConflictClick(schedule)}
            >
              <div className="font-semibold truncate">
                {schedule.subject.name}
              </div>
              <div className="text-xs truncate">
                {schedule.subject.code} - {schedule.subject.kelas}
              </div>
              <div className="text-xs truncate">
                {schedule.lecturers.map((l) => l.name).join(", ")}
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>{schedule.subject.name}</p>
            <p>
              {schedule.subject.code} - {schedule.subject.kelas}
            </p>
            <p>Room: {schedule.room_id}</p>
            <p>Lecturers: {schedule.lecturers.map((l) => l.name).join(", ")}</p>
            {schedule.is_conflicted && schedule.reason && (
              <p className="text-red-500">{schedule.reason}</p>
            )}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <Card className="flex flex-col h-full w-full p-2">
      <div className="flex p-4 border-b gap-x-4">
        <div className="flex flex-col sm:flex-row gap-4 w-full justify-between">
          <div className="flex gap-x-4">
            <Select value={selectedDay} onValueChange={setSelectedDay}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Select day" />
              </SelectTrigger>
              <SelectContent>
                {DAYS.map((day) => (
                  <SelectItem key={day} value={day}>
                    {day}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={selectedBuilding}
              onValueChange={setSelectedBuilding}
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Select building" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Buildings</SelectItem>
                {buildings.map((building, index) => (
                  <SelectItem key={building + index} value={building}>
                    {building}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {role === "admin" && (
            <Button>
              <Link href={"data-manajemen"} className="flex items-center gap-2">
                <Pencil /> Edit Timetable
              </Link>
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 relative">
        <div className="absolute inset-0 overflow-auto">
          <div className="inline-block min-w-full">
            <div
              className="grid"
              style={{
                gridTemplateColumns: `150px repeat(${
                  Object.values(roomsByBuilding).flat().length
                }, minmax(200px, 1fr))`,
              }}
            >
              <div className="sticky top-0 left-0 z-30 bg-gray-100 p-2 font-bold border-b border-r">
                Time
              </div>
              {Object.entries(roomsByBuilding).flatMap(
                ([building, buildingRooms]) =>
                  buildingRooms.map((room, index) => (
                    <div
                      key={`${room.id}-${index}`}
                      className="sticky top-0 z-20 p-2 font-bold text-center bg-gray-100 border-b truncate"
                    >
                      {room.id}
                    </div>
                  ))
              )}

              {uniqueTimeSlots.map((timeSlot) => (
                <React.Fragment key={timeSlot.id}>
                  <div className="sticky left-0 z-10 bg-white p-2 font-bold border">
                    {timeSlot.start_time} - {timeSlot.end_time}
                  </div>

                  {Object.entries(roomsByBuilding).flatMap(
                    ([building, buildingRooms]) =>
                      buildingRooms.map((room, index) => (
                        <div
                          key={`${room.id}-${timeSlot.id}-${index}`}
                          className="relative h-24 border"
                        >
                          {renderScheduleCard(
                            getScheduleForSlot(timeSlot, room.id),
                            timeSlot,
                            room.id
                          )}
                        </div>
                      ))
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4 p-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-300 rounded"></div>
          <span className="text-sm">No Conflicts</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span className="text-sm">Warning (Potential issues)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-300 rounded"></div>
          <span className="text-sm">Conflicts</span>
        </div>
      </div>
      {renderConflictModal()}
    </Card>
  );
};

export default TimeTableView;
