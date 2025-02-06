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
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Search, UserX2 } from "lucide-react";

const AdminPreferences = () => {
  const [timeSlots, setTimeSlots] = useState([]);
  const [preferences, setPreferences] = useState([]);
  const [selectedDay, setSelectedDay] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPreference, setSelectedPreference] = useState(null);
  const [dosenList, setDosenList] = useState([]);
  const [selectedDosen, setSelectedDosen] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [isDosenSelectOpen, setIsDosenSelectOpen] = useState(false);

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

  const reasonOptions = [
    "Personal preference",
    "Research project",
    "Family obligations",
    "Scheduling constraints",
  ];

  useEffect(() => {
    if (selectedDosen) {
      Promise.all([fetchTimeSlots(), fetchPreferences()]);
    }
  }, [selectedDay, selectedDosen]);

  const searchDosen = async (searchTerm) => {
    try {
      const response = await fetch(
        `http://localhost:8000/dosen/get-dosen/names?page=1&limit=50&filter=${searchTerm}`
      );
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setDosenList(data.data);
    } catch (error) {
      console.error("Error fetching dosen list:", error);
      setError("Failed to load dosen list");
    }
  };

  useEffect(() => {
    if (searchTerm) {
      const debounce = setTimeout(() => {
        searchDosen(searchTerm);
      }, 300);
      return () => clearTimeout(debounce);
    }
  }, [searchTerm]);

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
    if (!selectedDosen) return;

    try {
      const response = await fetch(
        `http://localhost:8000/preference/dosen/${selectedDosen.id}`
      );
      const data = await response.json();
      console.log("Fetched preferences:", data);
      data.forEach((pref) => {
        console.log("Preference high priority value:", {
          id: pref.id,
          is_high_priority: pref.is_high_priority,
          typeof_is_high_priority: typeof pref.is_high_priority,
        });
      });
      setPreferences(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching preferences:", error);
    } finally {
      setLoading(false);
    }
  };
  const handlePreferenceClick = (timeSlotId, isChecked) => {
    const existingPref = preferences.find((p) => p.timeslot_id === timeSlotId);
    console.log("Clicked preference:", {
      existingPref,
      is_high_priority: existingPref?.is_high_priority,
      typeof_is_high_priority: typeof existingPref?.is_high_priority,
    });

    if (isChecked) {
      setSelectedPreference(existingPref || { timeslot_id: timeSlotId });
      setIsModalOpen(true);
    } else if (existingPref) {
      handlePreferenceChange(timeSlotId, { delete: true });
    }
  };

  const handlePreferenceChange = async (timeSlotId, prefData = {}) => {
    if (!selectedDosen) return;
    console.log("Saving preference data:", {
      timeSlotId,
      prefData,
      is_high_priority: prefData.is_high_priority,
      typeof_is_high_priority: typeof prefData.is_high_priority,
    });
    try {
      const existingPref = preferences.find(
        (p) => p.timeslot_id === timeSlotId
      );

      if (prefData.delete) {
        await fetch(`http://localhost:8000/preference/${existingPref.id}`, {
          method: "DELETE",
        });
        setPreferences(preferences.filter((p) => p.id !== existingPref.id));
      } else if (existingPref) {
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
              dosen_id: selectedDosen.id,
              timeslot_id: timeSlotId,
            }),
          }
        );

        if (!response.ok) throw new Error("Failed to update preference");
        const updatedPref = await response.json();
        setPreferences(
          preferences.map((p) => (p.id === updatedPref.id ? updatedPref : p))
        );
      } else {
        const response = await fetch("http://localhost:8000/preference/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            dosen_id: selectedDosen.id,
            timeslot_id: timeSlotId,
            is_special_needs: false,
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

  const formatTime = (timeString) => {
    return timeString.slice(0, 5);
  };

  return (
    <div className="p-8 flex flex-col w-full">
      <h1 className="text-2xl font-bold mb-4">Manajemen Preferensi Dosen</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Pilih Dosen</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Input
                type="text"
                placeholder="Cari nama dosen..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <Button
              className="bg-primary"
              onClick={() => setIsDosenSelectOpen(true)}
            >
              Cari Dosen <Search />
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={isDosenSelectOpen} onOpenChange={setIsDosenSelectOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Pilih Dosen</DialogTitle>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID Dosen</TableHead>
                  <TableHead>Nama Dosen</TableHead>
                  <TableHead className="w-24">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dosenList.map((dosen) => (
                  <TableRow key={dosen.id}>
                    <TableCell>{dosen.id}</TableCell>
                    <TableCell>{dosen.nama}</TableCell>
                    <TableCell>
                      <Button
                        className="bg-primary"
                        onClick={() => {
                          setSelectedDosen(dosen);
                          setIsDosenSelectOpen(false);
                        }}
                      >
                        Pilih
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>

      {selectedDosen ? (
        <Card className="w-full">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Preferensi: {selectedDosen.nama}</span>
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
                          if (preference) {
                            console.log("Rendering preference:", {
                              timeSlot_id: timeSlot.id,
                              is_high_priority: preference.is_high_priority,
                              typeof_is_high_priority:
                                typeof preference.is_high_priority,
                            });
                          }
                          return (
                            <TableCell
                              key={`${day}-${timeRange.start}`}
                              className="text-center"
                            >
                              <div className="flex items-center justify-center group relative">
                                <Checkbox
                                  id="high-priority"
                                  checked={!!preference}
                                  onCheckedChange={(checked) =>
                                    handlePreferenceClick(timeSlot.id, checked)
                                  }
                                />
                                {preference && (
                                  <div
                                    className={`absolute hidden group-hover:block text-white text-xs rounded px-2 py-1 -top-8 whitespace-nowrap ${
                                      preference.is_high_priority
                                        ? "bg-red-500"
                                        : "bg-blue-500"
                                    }`}
                                  >
                                    {preference.is_high_priority
                                      ? `${
                                          preference.reason || "high priority"
                                        }`
                                      : "Prioritas Normal"}
                                  </div>
                                )}
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
        </Card>
      ) : (
        <Card className="w-full h-64 flex flex-col items-center justify-center space-y-4 bg-gray-50">
          <UserX2 className="w-12 h-12 text-gray-400" />
          <div className="text-lg font-medium text-gray-600">
            Silakan pilih dosen terlebih dahulu
          </div>
          <p className="text-sm text-gray-500">
            Pilih dosen untuk melihat preferensi jadwal
          </p>
        </Card>
      )}

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent
          className={`${
            selectedPreference?.is_high_priority === 1
              ? "border-t-4 border-t-red-500"
              : "border-t-4 border-t-blue-500"
          }`}
        >
          <DialogHeader>
            <DialogTitle
              className={`${
                selectedPreference?.is_high_priority === 1
                  ? "text-red-500"
                  : "text-blue-500"
              }`}
            >
              {selectedPreference?.is_high_priority === 1
                ? "Preferensi Prioritas Tinggi"
                : "Preferensi Normal"}
            </DialogTitle>
            <div className="text-sm text-gray-500">
              {selectedPreference?.is_high_priority === 1
                ? "Preferensi ini memiliki prioritas tinggi dan akan dipertimbangkan lebih dahulu dalam penjadwalan"
                : "Preferensi normal akan dipertimbangkan sesuai ketersediaan jadwal"}
            </div>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center gap-4">
              <Label
                htmlFor="high-priority"
                className={`${
                  selectedPreference?.is_high_priority === 1
                    ? "text-red-500"
                    : "text-blue-500"
                }`}
              >
                Prioritas Tinggi
              </Label>
              <Checkbox
                id="high-priority"
                checked={selectedPreference?.is_high_priority === 1}
                onCheckedChange={(checked) => {
                  console.log("Changing high priority to:", {
                    checked,
                    typeof_checked: typeof checked,
                    new_value: checked ? 1 : 0,
                  });
                  setSelectedPreference((prev) => ({
                    ...prev,
                    is_high_priority: checked ? 1 : 0,
                  }));
                }}
              />
            </div>
            <div className="grid gap-2">
              <Label
                className={
                  selectedPreference?.is_high_priority === 1
                    ? "text-red-500"
                    : "text-blue-500"
                }
              >
                {selectedPreference?.is_high_priority === 1
                  ? "Alasan Prioritas Tinggi"
                  : "Catatan (Opsional)"}
              </Label>
              <Select
                value={selectedPreference?.reason || ""}
                onValueChange={(value) => {
                  setSelectedPreference((prev) => ({
                    ...prev,
                    reason: value,
                  }));
                }}
                disabled={selectedPreference?.is_high_priority !== 1}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={
                      selectedPreference?.is_high_priority === 1
                        ? "Pilih alasan prioritas"
                        : "Tambahkan catatan"
                    }
                  />
                </SelectTrigger>
                <SelectContent className="bg-white">
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
              variant={
                selectedPreference?.is_high_priority === 1
                  ? "destructive"
                  : "default"
              }
            >
              Simpan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedDosen && (
        <div className="mt-6 space-y-4">
          <div className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <div className="h-4 w-4 bg-red-500 rounded" />
              <span className="text-sm text-gray-600">Prioritas Tinggi</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-4 w-4 bg-primary rounded" />
              <span className="text-sm text-gray-600">Preferensi Normal</span>
            </div>
          </div>

          <Alert>
            <AlertDescription>
              Anda sedang mengedit preferensi untuk dosen:{" "}
              <strong>{selectedDosen.nama}</strong>
            </AlertDescription>
          </Alert>
        </div>
      )}
    </div>
  );
};

export default AdminPreferences;
