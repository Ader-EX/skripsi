"use client";
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import toast from "react-hot-toast";

import DosenSelectionDialog from "@/components/global/DosenSelectionDialog";
import OpenedClassSelectionDialog from "@/components/global/OpenedClassSelectionDialog";
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/timetable`;
const TIMESLOT_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/timeslot/`;

const TimeTableForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const [timeslotList, setTimeslotList] = useState([]);
  const [isMatkulDialogOpen, setIsMatkulDialogOpen] = useState(false);
  const [isDosenDialogOpen, setIsDosenDialogOpen] = useState(false);
  const token = Cookies.get("access_token");

  // Default form data
  const defaultFormData = {
    matakuliah_id: "",
    matakuliah_nama: "",
    dosen_id: "",
    dosen_nama: "",
    timeslot_id: "",
    ruangan: "",
    kapasitas: 30,
    tahun_akademik: new Date().getFullYear(),
    semester: 1,
    is_active: true,
  };

  // Initialize form state with default or initialData
  const [formData, setFormData] = useState(defaultFormData);

  useEffect(() => {
    if (initialData) {
      setFormData({
        ...defaultFormData,
        ...initialData,
        matakuliah_id: initialData.matakuliah_id || "",
        matakuliah_nama: initialData.matakuliah_nama || "",
        dosen_id: initialData.dosen_id || "",
        dosen_nama: initialData.dosen_nama || "",
      });
    } else {
      setFormData(defaultFormData);
    }
  }, [initialData]);

  useEffect(() => {
    const fetchTimeslots = async () => {
      try {
        const response = await fetch(TIMESLOT_API_URL, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!response.ok) throw new Error("Failed to fetch timeslots");
        const data = await response.json();
        setTimeslotList(data);
      } catch (error) {
        console.error("Error fetching timeslots:", error);
      }
    };

    fetchTimeslots();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleMatkulSelect = (selectedMatkul) => {
    setFormData((prev) => ({
      ...prev,
      matakuliah_id: selectedMatkul.kodemk || "",
      matakuliah_nama: selectedMatkul.namamk || "",
    }));
  };

  const handleDosenSelect = (selectedDosen) => {
    setFormData((prev) => ({
      ...prev,
      dosen_id: selectedDosen.id || "",
      dosen_nama: selectedDosen.nama || "",
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const method = initialData ? "PUT" : "POST";
      const url = initialData ? `${API_URL}/${initialData.id}` : API_URL;

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
        initialData ? "Jadwal berhasil diupdate" : "Jadwal berhasil ditambahkan"
      );
      onSubmit();
      onClose();
    } catch (error) {
      console.error("Error submitting form:", error);
      toast.error("Error submitting form");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Jadwal" : "Tambah Jadwal"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="gap-4 grid grid-cols-2">
          {/* Mata Kuliah */}
          <div className="col-span-2">
            <Label>Mata Kuliah</Label>
            <div className="flex gap-2">
              <Input value={formData.matakuliah_nama || ""} readOnly />
              <Button onClick={() => setIsMatkulDialogOpen(true)}>Pilih</Button>
            </div>
          </div>

          <OpenedClassSelectionDialog
            isOpen={isMatkulDialogOpen}
            onClose={() => setIsMatkulDialogOpen(false)}
            onSelect={handleMatkulSelect}
          />

          {/* Dosen */}
          <div className="col-span-2">
            <Label>Dosen</Label>
            <div className="flex gap-2">
              <Input value={formData.dosen_nama || ""} readOnly />
              <Button onClick={() => setIsDosenDialogOpen(true)}>Pilih</Button>
            </div>
          </div>

          <DosenSelectionDialog
            isOpen={isDosenDialogOpen}
            onClose={() => setIsDosenDialogOpen(false)}
            onSelect={handleDosenSelect}
          />

          {/* Timeslots */}
          <div className="col-span-2">
            <Label>Timeslot</Label>
            <select
              name="timeslot_id"
              value={formData.timeslot_id || ""}
              onChange={handleChange}
              className="w-full border p-2"
              required
            >
              <option value="">Pilih Timeslot</option>
              {timeslotList.map((ts) => (
                <option key={ts.id} value={ts.id}>
                  {ts.day}, {ts.start_time} - {ts.end_time}
                </option>
              ))}
            </select>
          </div>

          {/* Ruangan */}
          <div>
            <Label>Ruangan</Label>
            <Input
              name="ruangan"
              value={formData.ruangan || ""}
              onChange={handleChange}
              required
            />
          </div>

          {/* Kapasitas */}
          <div>
            <Label>Kapasitas</Label>
            <Input
              name="kapasitas"
              type="number"
              value={formData.kapasitas || ""}
              onChange={handleChange}
              required
            />
          </div>

          {/* Submit Button */}
          <div className="col-span-2">
            <Button type="submit" className="w-full">
              {initialData ? "Simpan Perubahan" : "Tambah Jadwal"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default TimeTableForm;
