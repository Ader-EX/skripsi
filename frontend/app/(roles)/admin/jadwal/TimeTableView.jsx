import React, { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
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

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const TimeTableView = ({ schedules, rooms, timeSlots }) => {
  const [selectedDay, setSelectedDay] = useState("Monday");
  const [selectedBuilding, setSelectedBuilding] = useState("all");

  // Get unique time slots for Y-axis
  const uniqueTimeSlots = useMemo(() => {
    return timeSlots
      .filter(
        (slot, index, self) =>
          index === self.findIndex((s) => s.start_time === slot.start_time)
      )
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
      .filter((slot) => parseInt(slot.start_time.split(":")[0], 10) < 18); // Exclude times >= 18:00
  }, [timeSlots]);

  // Group rooms by building for filtering
  const roomsByBuilding = useMemo(() => {
    const buildings = rooms.reduce((acc, room) => {
      if (!acc[room.building]) {
        acc[room.building] = [];
      }
      acc[room.building].push(room);
      return acc;
    }, {});

    // Filter rooms if a building is selected
    if (selectedBuilding !== "all") {
      return {
        [selectedBuilding]: buildings[selectedBuilding],
      };
    }
    return buildings;
  }, [rooms, selectedBuilding]);

  // Get unique buildings for filter
  const buildings = useMemo(() => {
    return [...new Set(rooms.map((room) => room.building))];
  }, [rooms]);

  const getScheduleForSlot = (timeSlot, roomId) => {
    return schedules.filter(
      (schedule) =>
        schedule.room_id === roomId &&
        schedule.time_slots.some(
          (slot) =>
            slot.day === selectedDay && slot.start_time === timeSlot.start_time
        )
    );
  };
  const getScheduleHeight = (schedule, currentTimeSlot) => {
    if (!schedule?.time_slots || !currentTimeSlot?.start_time) return 4;

    const slots = schedule.time_slots.filter(
      (slot) =>
        slot?.day === selectedDay &&
        slot?.start_time === currentTimeSlot.start_time
    );
    return slots.length ? 4 : 0; // Return 4rem if slot exists, 0 if not
  };

  const renderScheduleCard = (scheduleList, timeSlot, roomId) => {
    if (!scheduleList.length) return null;

    return scheduleList.map((schedule, index) => (
      <TooltipProvider key={`${schedule.id}-${index}`}>
        <Tooltip>
          <TooltipTrigger asChild>
            <div
              className={`absolute w-full p-2 rounded text-xs ${
                scheduleList.length > 1 ? "bg-red-100" : "bg-green-100"
              }`}
              style={{
                height: `${getScheduleHeight(schedule)}rem`,
                left: scheduleList.length > 1 ? `${index * 50}%` : "0",
                width: scheduleList.length > 1 ? "50%" : "100%",
                zIndex: scheduleList.length > 1 ? index + 1 : 1,
              }}
            >
              <div className="font-semibold truncate">
                {schedule.subject.name}
              </div>
              <div className="truncate text-gray-600">
                {schedule.subject.code} - {schedule.subject.kelas}
              </div>
              <div className="truncate text-gray-500">
                {schedule.lecturers.map((l) => l.name.split(" ")[0]).join(", ")}
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <div className="font-bold">{schedule.subject.name}</div>
              <div>Code: {schedule.subject.code}</div>
              <div>Class: {schedule.subject.kelas}</div>
              <div>
                Lecturers: {schedule.lecturers.map((l) => l.name).join(", ")}
              </div>
              <div>Room: {roomId}</div>
              <div>
                Capacity: {schedule.student_count}/{schedule.max_capacity}
              </div>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    ));
  };

  return (
    <Card className="flex flex-col h-full">
      {/* Fixed header section */}
      <div className="flex-none p-4">
        <div className="flex gap-4">
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

          <Select value={selectedBuilding} onValueChange={setSelectedBuilding}>
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
      </div>
      <div className="flex-1 overflow-auto border-t p-4">
        <div className="inline-block min-w-full">
          <div
            className="grid gap-1"
            style={{
              gridTemplateColumns: `150px repeat(${
                Object.values(roomsByBuilding).flat().length
              }, minmax(200px, 1fr))`,
            }}
          >
            {/* Header Row */}
            <div className="sticky left-0  bg-gray-100 p-2 font-bold">Time</div>
            {Object.entries(roomsByBuilding).flatMap(
              ([building, buildingRooms]) =>
                buildingRooms.map((room, index) => (
                  <div
                    key={`${room.id}-${index}`}
                    className="p-2 font-bold text-center bg-gray-100 truncate"
                  >
                    {room.id}
                  </div>
                ))
            )}

            {/* Time slots row-wise */}
            {uniqueTimeSlots.map((timeSlot) => (
              <React.Fragment key={timeSlot.id}>
                {/* Time column with high z-index */}
                <div className="sticky left-0 bg-white p-2 border-r font-bold border ">
                  {timeSlot.start_time} - {timeSlot.end_time}
                </div>

                {/* Rooms horizontally */}
                {Object.entries(roomsByBuilding).flatMap(
                  ([building, buildingRooms]) =>
                    buildingRooms.map((room, index) => (
                      <div
                        key={`${room.id}-${timeSlot.id}-${index}`}
                        className="relative h-16 border w-full"
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
    </Card>
  );
};

export default TimeTableView;
