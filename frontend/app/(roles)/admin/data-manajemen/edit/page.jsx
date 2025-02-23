"use client";
import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import OpenedClassSelectionDialog from "@/components/global/OpenedClassSelectionDialog";
import RuanganSelectionDialog from "@/components/global/RuanganSelectionDialog";
import TimeslotSelectionTable from "./TimeslotSelectionTable";
import toast from "react-hot-toast";
import { Label } from "@/components/ui/label";
import { Pencil } from "lucide-react";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const EditTimetable = () => {
  const router = useRouter();
  const searchParams = typeof window !== "undefined" ? useSearchParams() : null;
  const timetableId = searchParams ? searchParams.get("id") : null;

  const [selectedOpenedClass, setSelectedOpenedClass] = useState(null);
  const [selectedRuangan, setSelectedRuangan] = useState(null);
  const [selectedTimeslots, setSelectedTimeslots] = useState([]);
  const [availableTimeslots, setAvailableTimeslots] = useState([]);
  const [isOpenedClassDialogOpen, setIsOpenedClassDialogOpen] = useState(false);
  const [isRuanganDialogOpen, setIsRuanganDialogOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  const token = Cookies.get("access_token");
  if (!token) {
    window.location.href = "/";
  }

  useEffect(() => {
    setIsMounted(true);
    if (timetableId) {
      fetchTimetableDetails(timetableId);
    }
  }, [timetableId]);

  const fetchTimetableDetails = async (id) => {
    try {
      const response = await fetch(`${API_URL}/timetable/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch timetable details");

      const data = await response.json();
      setSelectedOpenedClass({
        id: data.opened_class_id,
        nama_mk: data.mata_kuliah_nama, // Ensure this data exists in the API
        kelas: data.kelas,
      });
      setSelectedRuangan({
        id: data.ruangan_id,
        nama_ruang: data.ruangan_nama, // Ensure this data exists in the API
      });
      setSelectedTimeslots(data.timeslot_ids);

      fetchRuanganDetails(data.ruangan_id);
    } catch (error) {
      console.error("Error fetching timetable:", error);
    }
  };

  const fetchRuanganDetails = async (ruanganId) => {
    try {
      const response = await fetch(
        `${API_URL}/ruangan/timeslots/availability?ruangan_id=${ruanganId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Failed to fetch room timeslots");

      const data = await response.json();
      setAvailableTimeslots(data);
    } catch (error) {
      console.error("Error fetching room timeslots:", error);
    }
  };

  const handleOpenedClassSelect = (openedClass) => {
    setSelectedOpenedClass({
      id: openedClass.id,
      nama_mk: openedClass.mata_kuliah.nama,
      kelas: openedClass.kelas,
    });
  };

  const handleRuanganSelect = (ruangan) => {
    setSelectedRuangan({
      id: ruangan.id,
      nama_ruang: ruangan.nama_ruang,
    });
    fetchRuanganDetails(ruangan.id);
  };

  const handleTimeslotToggle = (timeslotId) => {
    setSelectedTimeslots((prevSelected) =>
      prevSelected.includes(timeslotId)
        ? prevSelected.filter((id) => id !== timeslotId)
        : [...prevSelected, timeslotId]
    );
  };

  const handleSubmit = async () => {
    if (
      !selectedOpenedClass ||
      !selectedRuangan ||
      selectedTimeslots.length === 0
    ) {
      toast.error(
        "Please select an Opened Class, Room, and at least one Timeslot."
      );
      return;
    }

    try {
      const method = timetableId ? "PUT" : "POST";
      const url = timetableId
        ? `${API_URL}/timetable/${timetableId}`
        : `${API_URL}/timetable`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          opened_class_id: selectedOpenedClass.id,
          ruangan_id: selectedRuangan.id,
          timeslot_ids: selectedTimeslots,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json(); // ✅ Read the error response
        throw new Error(errorData.detail || "Failed to save timetable");
      }

      toast.success("Timetable saved successfully!");
      router.push("/admin/data-manajemen");
    } catch (error) {
      toast.error(error.message || "Error saving timetable");
    }
  };

  if (!isMounted) return null;

  return (
    <div className="p-8 flex flex-col w-full gap-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex gap-x-2 text-blue-500 items-center ">
            <Pencil className="w-4 " />
            Timetable Editor
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Opened Class Input */}
          <div className="mb-4">
            <Label>Kelas Yang Dibuka</Label>
            <Input
              value={
                selectedOpenedClass
                  ? `${selectedOpenedClass.id} - ${selectedOpenedClass.nama_mk} - ${selectedOpenedClass.kelas}`
                  : ""
              }
              placeholder="Select Opened Class"
              readOnly
              onClick={() => setIsOpenedClassDialogOpen(true)}
              className="w-full cursor-pointer"
            />
          </div>

          {/* Room Input */}
          <div className="mb-4">
            <Label>Ruangan</Label>
            <Input
              value={
                selectedRuangan
                  ? `${selectedRuangan.id} - ${selectedRuangan.nama_ruang}`
                  : ""
              }
              placeholder="Select Room"
              readOnly
              onClick={() => setIsRuanganDialogOpen(true)}
              className="w-full cursor-pointer"
            />
          </div>
        </CardContent>
      </Card>
      {availableTimeslots.length > 0 && (
        <Card className="p-6">
          <TimeslotSelectionTable
            availableTimeslots={availableTimeslots}
            selectedTimeslots={selectedTimeslots}
            onTimeslotToggle={handleTimeslotToggle}
            timetableTimeslots={selectedTimeslots} // Pass previously selected timeslots
          />
        </Card>
      )}

      <Button onClick={handleSubmit} className="mt-6 bg-primary">
        Save Timetable
      </Button>

      <OpenedClassSelectionDialog
        isOpen={isOpenedClassDialogOpen}
        onClose={() => setIsOpenedClassDialogOpen(false)}
        onSelect={handleOpenedClassSelect}
      />

      <RuanganSelectionDialog
        isOpen={isRuanganDialogOpen}
        onClose={() => setIsRuanganDialogOpen(false)}
        onSelect={handleRuanganSelect}
      />
    </div>
  );
};

export default EditTimetable;
