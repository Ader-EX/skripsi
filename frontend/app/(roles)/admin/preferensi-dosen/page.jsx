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

  const reasonOptions = [
    "Jadwal bentrok",
    "Tanggung jawab lain",
    "Kesehatan",
    "Jadwal luar kampus",
    "Bimbingan skripsi",
    "Beban kerja tinggi",
    "Hanya bisa di slot ini",
  ];

  useEffect(() => {
    if (selectedDosen) {
      Promise.all([fetchTimeSlots(), fetchPreferences()]);
    }
  }, [selectedDay, selectedDosen]);

  const searchDosen = async (searchTerm) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/dosen/get-dosen/names?page=1&limit=50&filter=${searchTerm}`
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
          ? `${process.env.NEXT_PUBLIC_API_URL}/timeslot/`
          : `${process.env.NEXT_PUBLIC_API_URL}/timeslot/?day=${selectedDay}`;

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
        `${process.env.NEXT_PUBLIC_API_URL}/preference/dosen/${selectedDosen.id}`
      );
      const data = await response.json();
      setPreferences(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching preferences:", error);
    } finally {
      setLoading(false);
    }
  };

  const handlePreferenceClick = (timeSlotId, isChecked) => {
    const existingPref = preferences.find((p) => p.timeslot_id === timeSlotId);

    if (isChecked) {
      setSelectedPreference(existingPref || { timeslot_id: timeSlotId });
      setIsModalOpen(true);
    } else if (existingPref) {
      handlePreferenceChange(timeSlotId, { delete: true });
    }
  };

  const handlePreferenceChange = async (timeSlotId, prefData = {}) => {
    if (!selectedDosen) return;

    try {
      const existingPref = preferences.find(
        (p) => p.timeslot_id === timeSlotId
      );

      if (prefData.delete) {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/preference/${existingPref.id}`,
          {
            method: "DELETE",
          }
        );
        setPreferences(preferences.filter((p) => p.id !== existingPref.id));
      } else if (existingPref) {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/preference/${existingPref.id}`,
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
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/preference/`,
          {
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
          }
        );

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

  const uniqueDays = [...new Set(timeSlots.map((slot) => slot.day))];

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
                  {uniqueDays.map((day) => (
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
                    {uniqueDays.map((day) => (
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
                        colSpan={uniqueDays.length + 1}
                        className="text-center h-32"
                      >
                        <div className="flex items-center justify-center">
                          Loading...
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    Object.values(
                      timeSlots.reduce((acc, slot) => {
                        if (!acc[slot.start_time]) acc[slot.start_time] = {};
                        acc[slot.start_time][slot.day] = slot;
                        return acc;
                      }, {})
                    ).map((timeSlotGroup, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">
                          {formatTime(
                            Object.values(timeSlotGroup)[0].start_time
                          )}{" "}
                          -{" "}
                          {formatTime(Object.values(timeSlotGroup)[0].end_time)}
                        </TableCell>

                        {uniqueDays.map((day) => {
                          const timeSlot = timeSlotGroup[day];

                          if (!timeSlot) {
                            return <TableCell key={`${day}-${index}`} />;
                          }

                          const preference = preferences.find(
                            (p) => p.timeslot_id === timeSlot.id
                          );

                          return (
                            <TableCell
                              key={`${day}-${timeSlot.id}`}
                              className="text-center"
                            >
                              <div className="flex items-center justify-center group relative">
                                <Checkbox
                                  id={`preference-${timeSlot.id}`}
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
