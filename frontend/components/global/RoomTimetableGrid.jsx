"use client";
import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import toast from "react-hot-toast";
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/algorithm/formatted-timetable`;
const TIMESLOT_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/timeslot/`;
const OPENED_CLASS_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/opened-class/get-all`;
const RUANGAN_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/ruangan/`;

const EditTimetable = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const timetableId = searchParams.get("id");

  const [timeslotList, setTimeslotList] = useState([]);
  const [openedClassList, setOpenedClassList] = useState([]);
  const [ruanganList, setRuanganList] = useState([]);
  const token = Cookies.get("access_token");

  const defaultFormData = {
    opened_class_id: "",
    mata_kuliah_nama: "",
    kelas: "",
    ruangan_id: "",
    ruangan_nama: "",
    timeslot_ids: [], // ✅ Multiple timeslot selection
    sks: 3,
  };

  const [formData, setFormData] = useState(defaultFormData);

  // Fetch Timetable Data (if editing)
  useEffect(() => {
    if (timetableId) {
      fetch(`${API_URL}/${timetableId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.json())
        .then((data) => {
          if (
            !data ||
            !data.opened_class_id ||
            !data.ruangan_id ||
            !data.timeslot_ids
          ) {
            throw new Error("Invalid response structure");
          }

          setFormData({
            opened_class_id: data.opened_class_id,
            mata_kuliah_nama:
              data.opened_class?.mata_kuliah?.namamk || "Unknown Course",
            kelas: data.kelas,
            ruangan_id: data.ruangan_id,
            ruangan_nama: data.ruangan?.kode_ruangan || "",
            timeslot_ids: data.timeslot_ids, // ✅ Store timeslots as an array
            sks: data.opened_class?.mata_kuliah?.sks || 3,
          });
        })
        .catch((error) => {
          console.error("🚨 Error fetching timetable:", error);
          toast.error("Failed to load timetable data.");
        });
    }
  }, [timetableId]);

  // Fetch Options (Timeslots, Opened Classes, Rooms)
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [timeslots, openedClasses, ruangans] = await Promise.all([
          fetch(TIMESLOT_API_URL, {
            headers: { Authorization: `Bearer ${token}` },
          }).then((res) => res.json()),
          fetch(`${OPENED_CLASS_API_URL}?page=1&limit=50`, {
            headers: { Authorization: `Bearer ${token}` },
          }).then((res) => res.json()),
          fetch(`${RUANGAN_API_URL}?page=1&page_size=50`, {
            headers: { Authorization: `Bearer ${token}` },
          }).then((res) => res.json()),
        ]);
        setTimeslotList(timeslots);
        setOpenedClassList(openedClasses.data);
        setRuanganList(ruangans.data);
      } catch (error) {
        console.error("🚨 Error fetching dropdown data:", error);
      }
    };

    fetchData();
  }, []);

  // Handle Room Selection
  const handleRoomSelect = (roomId) => {
    setFormData((prev) => ({
      ...prev,
      ruangan_id: roomId,
      ruangan_nama:
        ruanganList.find((r) => r.id === roomId)?.kode_ruangan || "",
    }));
  };

  // Handle Opened Class Selection
  const handleOpenedClassSelect = (classId) => {
    const selectedClass = openedClassList.find((oc) => oc.id === classId);
    setFormData((prev) => ({
      ...prev,
      opened_class_id: classId,
      mata_kuliah_nama: selectedClass?.mata_kuliah?.namamk || "",
      sks: selectedClass?.mata_kuliah?.sks || 3, // ✅ Update SKS dynamically
    }));
  };

  // Handle Timeslot Selection
  const handleSlotSelect = (selectedIds) => {
    if (selectedIds.length > formData.sks) {
      toast.error(`You can only select ${formData.sks} timeslots.`);
      return;
    }

    setFormData((prev) => ({
      ...prev,
      timeslot_ids: selectedIds,
    }));
  };

  // Handle Submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const method = timetableId ? "PUT" : "POST";
      const url = timetableId ? `${API_URL}/${timetableId}` : API_URL;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        throw new Error("Failed to submit timetable data");
      }

      toast.success(
        timetableId
          ? "Jadwal berhasil diperbarui"
          : "Jadwal berhasil ditambahkan"
      );
      router.push("/timetable");
    } catch (error) {
      console.error("🚨 Error submitting form:", error);
      toast.error("Gagal menyimpan jadwal");
    }
  };

  return (
    <div className="p-6 space-y-6 flex flex-col">
      <h1 className="text-2xl font-bold">
        {timetableId ? "Edit Jadwal" : "Tambah Jadwal"}
      </h1>

      {/* Opened Class Selection */}
      <div>
        <Label>Kelas</Label>
        <Select
          value={formData.opened_class_id}
          onValueChange={handleOpenedClassSelect}
          required
        >
          <SelectTrigger>
            <SelectValue placeholder="Pilih Kelas" />
          </SelectTrigger>
          <SelectContent>
            {openedClassList.map((oc) => (
              <SelectItem key={oc.id} value={oc.id}>
                {oc.mata_kuliah.namamk} - {oc.kelas}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Room Selection */}
      <div>
        <Label>Ruangan</Label>
        <Select
          value={formData.ruangan_id}
          onValueChange={handleRoomSelect}
          required
        >
          <SelectTrigger>
            <SelectValue placeholder="Pilih Ruangan" />
          </SelectTrigger>
          <SelectContent>
            {ruanganList.map((ruang) => (
              <SelectItem key={ruang.id} value={ruang.id}>
                {ruang.kode_ruangan}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Timeslot Selection (Multi-Select) */}
      <div>
        <Label>Timeslot</Label>
        <Select
          multiple
          value={formData.timeslot_ids}
          onValueChange={handleSlotSelect}
          required
        >
          <SelectTrigger>
            <SelectValue placeholder="Pilih Timeslot" />
          </SelectTrigger>
          <SelectContent>
            {timeslotList.map((ts) => (
              <SelectItem key={ts.id} value={ts.id}>
                {ts.day}, {ts.start_time} - {ts.end_time}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Submit Button */}
      <Button type="submit" onClick={handleSubmit} className="w-full">
        {timetableId ? "Simpan Perubahan" : "Tambah Jadwal"}
      </Button>
    </div>
  );
};

export default EditTimetable;
