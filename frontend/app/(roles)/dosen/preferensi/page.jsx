"use client";
import React, { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import Cookies from "js-cookie";
import { decodeToken } from "@/utils/decoder";

const DosenPreferensi = () => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [preferences, setPreferences] = useState([]);
  const [selectedDay, setSelectedDay] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPreference, setSelectedPreference] = useState(null);
  const [isSpecialNeeds, setIsSpecialNeeds] = useState(false);
  const [userId, setUserId] = useState(null); // Add state for userId
  const [userRole, setUserRole] = useState(null); // Add state for userRole

  useEffect(() => {
    const token = Cookies.get("access_token");
    if (token) {
      const payload = decodeToken(token);
      if (payload) {
        const encodedEmail = encodeURIComponent(payload.sub);
        fetch(`http://localhost:8000/user/details?email=${encodedEmail}`)
          .then((response) => response.json())
          .then((data) => {
            setUserId(data.id); // Set the user ID
            setUserRole(data.role); // Set the user role
          })
          .catch((error) => {
            console.error("Error fetching user details:", error);
          });
      }
    }
  }, []);

  // Predefined reasons
  const reasonOptions = [
    "Personal preference",
    "Research project",
    "Family obligations",
    "Scheduling constraints",
  ];

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const timeRanges = [
    { start: "08:00:00", end: "08:50:00" },
    { start: "08:50:00", end: "09:40:00" },
    { start: "09:40:00", end: "10:30:00" },
    { start: "10:30:00", end: "11:20:00" },
    { start: "13:00:00", end: "13:50:00" },
    { start: "13:50:00", end: "14:40:00" },
    { start: "14:40:00", end: "15:30:00" },
    { start: "15:30:00", end: "16:20:00" },
    { start: "16:20:00", end: "17:10:00" },
    { start: "17:10:00", end: "18:00:00" },
  ];

  useEffect(() => {
    if (userId) {
      Promise.all([fetchTimeSlots(), fetchPreferences()]);
    }
  }, [selectedDay, userId]);

  const fetchTimeSlots = async () => {
    try {
      const url =
        selectedDay === "all"
          ? "http://localhost:8000/timeslot/"
          : `http://localhost:8000/timeslot/?day=${selectedDay}`;

      const response = await fetch(url);
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setTimeSlots(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching time slots:", error);
      setError("Failed to load time slots");
    }
  };

  const fetchPreferences = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/preference/dosen/${userId}`
      );
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setPreferences(Array.isArray(data) ? data : []);

      if (data.length > 0) {
        setIsSpecialNeeds(data[0].is_special_needs);
      }
    } catch (error) {
      console.error("Error fetching preferences:", error);
      setError("Failed to load preferences");
    } finally {
      setLoading(false);
    }
  };

  const handlePreferenceClick = (timeSlotId) => {
    const existingPref = preferences.find((p) => p.timeslot_id === timeSlotId);
    if (existingPref) {
      setSelectedPreference(existingPref);
      setIsModalOpen(true);
    } else {
      handlePreferenceChange(timeSlotId);
    }
  };

  const handlePreferenceChange = async (timeSlotId, prefData = {}) => {
    console.log(userId + "preference data + " + " + timeSlotId " + timeSlotId);
    try {
      const existingPref = preferences.find(
        (p) => p.timeslot_id === timeSlotId
      );

      if (existingPref && !prefData) {
        // DELETE preference if unchecked
        await fetch(`http://localhost:8000/preference/${existingPref.id}`, {
          method: "DELETE",
        });
        setPreferences(preferences.filter((p) => p.id !== existingPref.id));
      } else if (existingPref) {
        // UPDATE existing preference
        const response = await fetch(
          `http://localhost:8000/preference/${existingPref.id}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              ...existingPref,
              ...prefData,
              dosen_id: userId, // ✅ Ensure dosen_id is sent
              timeslot_id: timeSlotId, // ✅ Ensure timeslot_id is sent
            }),
          }
        );

        if (!response.ok) throw new Error("Failed to update preference");
        const updatedPref = await response.json();
        setPreferences(
          preferences.map((p) => (p.id === updatedPref.id ? updatedPref : p))
        );
      } else {
        // CREATE new preference
        const response = await fetch("http://localhost:8000/preference/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            dosen_id: userId, // ✅ Include dosen_id
            timeslot_id: timeSlotId, // ✅ Include timeslot_id
            is_special_needs: isSpecialNeeds,
            is_high_priority: false,
            ...prefData,
          }),
        });

        if (!response.ok) throw new Error("Failed to create preference");
        const newPref = await response.json();
        setPreferences([...preferences, newPref]);
      }
    } catch (error) {
      console.error("Error updating preference:", error);
      setError("Failed to update preference");
    }
  };

  const handleSpecialNeedsChange = async (checked) => {
    setIsSpecialNeeds(checked);
    try {
      // Update all existing preferences
      const updatePromises = preferences.map((pref) =>
        fetch(`http://localhost:8000/preference/${pref.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...pref,
            is_special_needs: checked,
          }),
        })
      );

      await Promise.all(updatePromises);
      await fetchPreferences(); // Refresh preferences
    } catch (error) {
      console.error("Error updating special needs status:", error);
      setError("Failed to update special needs status");
    }
  };

  const formatTime = (timeString) => {
    return timeString.slice(0, 5);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Preferensi Jadwal Mengajar</h1>
      <p className="text-gray-600 mb-6">
        Silakan atur preferensi jadwal mengajar Anda untuk semester ini. Anda
        dapat memilih waktu yang tersedia dan memberikan alasan jika diperlukan.
      </p>

      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="special-needs"
                checked={isSpecialNeeds}
                onCheckedChange={handleSpecialNeedsChange}
              />
              <Label htmlFor="special-needs">
                Apakah Anda memiliki kondisi khusus yang memerlukan penempatan
                ruangan dekat dengan ruang dosen?
              </Label>
            </div>
          </div>
          <CardTitle className="flex items-center justify-between">
            <span>Pilih Hari dan Waktu</span>
            <Select value={selectedDay} onValueChange={setSelectedDay}>
              <SelectTrigger className="w-[180px] bg-white">
                <SelectValue placeholder="Pilih hari" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Hari</SelectItem>
                {days.map((day) => (
                  <SelectItem key={day} value={day}>
                    {day}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px]">Waktu</TableHead>
                  {days.map((day) => (
                    <TableHead key={day} className="text-center">
                      {day}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell
                      colSpan={days.length + 1}
                      className="text-center h-32"
                    >
                      <div className="flex items-center justify-center">
                        Loading...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  timeRanges.map((timeRange) => (
                    <TableRow key={`${timeRange.start}-${timeRange.end}`}>
                      <TableCell className="font-medium">
                        {formatTime(timeRange.start)} -{" "}
                        {formatTime(timeRange.end)}
                      </TableCell>
                      {days.map((day) => {
                        const timeSlot = timeSlots.find(
                          (slot) =>
                            slot.day === day &&
                            slot.start_time === timeRange.start &&
                            slot.end_time === timeRange.end
                        );

                        if (!timeSlot)
                          return (
                            <TableCell key={`${day}-${timeRange.start}`} />
                          );

                        const preference = preferences.find(
                          (p) => p.timeslot_id === timeSlot.id
                        );

                        return (
                          <TableCell
                            key={`${day}-${timeRange.start}`}
                            className="text-center"
                          >
                            <div className="flex items-center justify-center">
                              <Checkbox
                                checked={!!preference}
                                onCheckedChange={() =>
                                  handlePreferenceClick(timeSlot.id)
                                }
                                className={`h-4 w-4 ${
                                  preference?.is_high_priority
                                    ? "bg-red-500"
                                    : ""
                                }`}
                              />
                            </div>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>

        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Preferensi</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="flex items-center gap-4">
                <Label htmlFor="high-priority">Prioritas Tinggi</Label>
                <Checkbox
                  id="high-priority"
                  checked={selectedPreference?.is_high_priority}
                  onCheckedChange={(checked) => {
                    setSelectedPreference((prev) => ({
                      ...prev,
                      is_high_priority: checked,
                    }));
                  }}
                />
              </div>
              <div className="grid gap-2">
                <Label>Alasan</Label>
                <Select
                  value={selectedPreference?.reason || ""}
                  onValueChange={(value) => {
                    setSelectedPreference((prev) => ({
                      ...prev,
                      reason: value,
                    }));
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Pilih alasan" />
                  </SelectTrigger>
                  <SelectContent>
                    {reasonOptions.map((reason) => (
                      <SelectItem key={reason} value={reason}>
                        {reason}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                Batal
              </Button>
              <Button
                onClick={() => {
                  handlePreferenceChange(selectedPreference.timeslot_id, {
                    is_high_priority: selectedPreference.is_high_priority,
                    reason: selectedPreference.reason,
                  });
                  setIsModalOpen(false);
                }}
              >
                Simpan
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Card>
    </div>
  );
};

export default DosenPreferensi;
