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

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/timetable`;
const DOSEN_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/dosen`;
const MATKUL_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/matakuliah`;

const TimeTableForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const [dosenList, setDosenList] = useState([]);
  const [matkulList, setMatkulList] = useState([]);

  const [formData, setFormData] = useState(
    initialData || {
      matakuliah_id: "",
      dosen_id: "",
      hari: "Senin",
      waktu_mulai: "",
      waktu_selesai: "",
      ruangan: "",
      kapasitas: 30,
      tahun_akademik: new Date().getFullYear(),
      semester: 1,
      is_active: true,
    }
  );

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({
        matakuliah_id: "",
        dosen_id: "",
        hari: "Senin",
        waktu_mulai: "",
        waktu_selesai: "",
        ruangan: "",
        kapasitas: 30,
        tahun_akademik: new Date().getFullYear(),
        semester: 1,
        is_active: true,
      });
    }
  }, [initialData]);

  useEffect(() => {
    const fetchDosen = async () => {
      try {
        const response = await fetch(DOSEN_API_URL);
        if (!response.ok) throw new Error("Failed to fetch dosen");
        const data = await response.json();
        setDosenList(data);
      } catch (error) {
        console.error("Error fetching dosen:", error);
      }
    };

    const fetchMatkul = async () => {
      try {
        const response = await fetch(MATKUL_API_URL);
        if (!response.ok) throw new Error("Failed to fetch matakuliah");
        const data = await response.json();
        setMatkulList(data);
      } catch (error) {
        console.error("Error fetching matakuliah:", error);
      }
    };

    fetchDosen();
    fetchMatkul();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const method = initialData ? "PUT" : "POST";
      const url = initialData ? `${API_URL}/${initialData.id}` : API_URL;

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to submit time table data");
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
          <div className="col-span-2">
            <Label>Mata Kuliah</Label>
            <select
              name="matakuliah_id"
              value={formData.matakuliah_id}
              onChange={handleChange}
              className="w-full border p-2"
              required
            >
              <option value="">Pilih Mata Kuliah</option>
              {matkulList.map((matkul) => (
                <option key={matkul.id} value={matkul.id}>
                  {matkul.nama}
                </option>
              ))}
            </select>
          </div>

          <div className="col-span-2">
            <Label>Dosen</Label>
            <select
              name="dosen_id"
              value={formData.dosen_id}
              onChange={handleChange}
              className="w-full border p-2"
              required
            >
              <option value="">Pilih Dosen</option>
              {dosenList.map((dosen) => (
                <option key={dosen.id} value={dosen.id}>
                  {dosen.user?.fullname}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label>Hari</Label>
            <select
              name="hari"
              value={formData.hari}
              onChange={handleChange}
              className="w-full border p-2"
              required
            >
              {["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"].map(
                (day) => (
                  <option key={day} value={day}>
                    {day}
                  </option>
                )
              )}
            </select>
          </div>

          <div>
            <Label>Ruangan</Label>
            <Input
              name="ruangan"
              value={formData.ruangan}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Waktu Mulai</Label>
            <Input
              name="waktu_mulai"
              type="time"
              value={formData.waktu_mulai}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Waktu Selesai</Label>
            <Input
              name="waktu_selesai"
              type="time"
              value={formData.waktu_selesai}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Kapasitas</Label>
            <Input
              name="kapasitas"
              type="number"
              value={formData.kapasitas}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Tahun Akademik</Label>
            <Input
              name="tahun_akademik"
              type="number"
              value={formData.tahun_akademik}
              onChange={handleChange}
              required
            />
          </div>

          <div className="col-span-2">
            <Label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
              />
              Status Aktif
            </Label>
          </div>

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
