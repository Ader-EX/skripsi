"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import DosenTable from "./DosenTable";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

import toast from "react-hot-toast";
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/dosen`;
const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi`;
const DosenForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const [programStudiList, setProgramStudiList] = useState([]);
  const [formData, setFormData] = useState(
    initialData || {
      fullname: "",
      email: "",
      password: "",
      nim_nip: "",
      pegawai_id: "",
      nidn: "",
      nomor_ktp: "",
      nama: "",
      tanggal_lahir: "",
      progdi_id: "",
      ijin_mengajar: true,
      jabatan: "",
      title_depan: "",
      title_belakang: "",
      jabatan_id: "",
      is_sekdos: false,
    }
  );
  const token = Cookies.get("access_token");
  if (!token) {
    window.location.href = "/";
    return;
  }

  useEffect(() => {
    if (initialData) {
      setFormData({
        email: initialData.email || "",
        password: initialData.password || "",
        nim_nip: initialData.nim_nip || "",
        pegawai_id: initialData.pegawai_id || "",
        nidn: initialData.nidn || "",
        nomor_ktp: initialData.nomor_ktp || "",
        nama: initialData.nama || "",
        tanggal_lahir: initialData.tanggal_lahir || "",
        progdi_id: initialData.progdi_id || "",
        ijin_mengajar:
          initialData.ijin_mengajar !== undefined
            ? initialData.ijin_mengajar
            : true,
        jabatan: initialData.jabatan || "",
        title_depan: initialData.title_depan || "",
        title_belakang: initialData.title_belakang || "",
        jabatan_id: initialData.jabatan_id || "",
        is_sekdos:
          initialData.is_sekdos !== undefined ? initialData.is_sekdos : false,
      });
    } else {
      setFormData({
        email: "",
        password: "",
        nim_nip: "",
        pegawai_id: "",
        nidn: "",
        nomor_ktp: "",
        nama: "",
        tanggal_lahir: "",
        progdi_id: "",
        ijin_mengajar: true,
        jabatan: "",
        title_depan: "",
        title_belakang: "",
        jabatan_id: "",
        is_sekdos: false,
      });
    }
  }, [initialData]);

  useEffect(() => {
    const fetchProgramStudi = async () => {
      try {
        const response = await fetch(PROGRAM_STUDI_API_URL, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) throw new Error("Failed to fetch program studi");
        const data = await response.json();
        setProgramStudiList(data);
      } catch (error) {
        console.error("Error fetching program studi:", error);
      }
    };

    fetchProgramStudi();
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

    const formattedData = {
      ...formData,
      tanggal_lahir: new Date(formData.tanggal_lahir)
        .toLocaleDateString("en-GB")
        .split("/")
        .join("/"),
    };

    onSubmit(formattedData);
  };
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Dosen" : "Tambah Dosen"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="gap-4 grid grid-cols-3">
          {/* ✅ Nama */}
          <div className="col-span-3">
            <Label>Nama</Label>
            <Input
              name="nama"
              value={formData.nama}
              onChange={handleChange}
              required
            />
          </div>

          {/* ✅ Email */}
          <div>
            <Label>Email</Label>
            <Input
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          {/* ✅ NIM/NIP */}
          <div>
            <Label>NIM/NIP</Label>
            <Input
              name="nim_nip"
              value={formData.nim_nip}
              onChange={handleChange}
              required
            />
          </div>

          {/* ✅ Password (Only show for new dosen) */}
          {!initialData && (
            <div>
              <Label>Password</Label>
              <Input
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
          )}

          {/* ✅ Pegawai ID */}
          <div>
            <Label>Pegawai ID</Label>
            <Input
              name="pegawai_id"
              type="number"
              value={formData.pegawai_id}
              onChange={handleChange}
            />
          </div>

          {/* ✅ NIDN */}
          <div>
            <Label>NIDN</Label>
            <Input name="nidn" value={formData.nidn} onChange={handleChange} />
          </div>

          {/* ✅ Nomor KTP */}
          <div>
            <Label>Nomor KTP</Label>
            <Input
              name="nomor_ktp"
              value={formData.nomor_ktp}
              onChange={handleChange}
            />
          </div>

          {/* ✅ Tanggal Lahir */}
          <div>
            <Label>Tanggal Lahir</Label>
            <Input
              name="tanggal_lahir"
              type="date"
              value={formData.tanggal_lahir}
              onChange={handleChange}
              required
            />
          </div>

          {/* ✅ Program Studi (Dropdown) */}
          <div>
            <Label>Program Studi</Label>
            <select
              name="progdi_id"
              value={formData.progdi_id}
              onChange={handleChange}
              className="w-full border p-2"
              required
            >
              <option value="">Pilih Program Studi</option>
              {programStudiList.map((prog) => (
                <option key={prog.id} value={prog.id}>
                  {prog.name}
                </option>
              ))}
            </select>
          </div>

          {/* ✅ Izin Mengajar (Dropdown) */}
          <div>
            <Label>Izin Mengajar</Label>
            <select
              name="ijin_mengajar"
              value={formData.ijin_mengajar.toString()}
              onChange={handleChange}
              className="w-full border p-2"
            >
              <option value="true">Ya</option>
              <option value="false">Tidak</option>
            </select>
          </div>

          {/* ✅ Jabatan */}
          <div>
            <Label>Jabatan</Label>
            <Input
              name="jabatan"
              value={formData.jabatan}
              onChange={handleChange}
            />
          </div>

          {/* ✅ Jabatan ID */}
          <div>
            <Label>Jabatan ID</Label>
            <Input
              name="jabatan_id"
              type="number"
              value={formData.jabatan_id}
              onChange={handleChange}
            />
          </div>

          {/* ✅ Title Depan */}
          <div>
            <Label>Title Depan</Label>
            <Input
              name="title_depan"
              value={formData.title_depan}
              onChange={handleChange}
            />
          </div>

          {/* ✅ Title Belakang */}
          <div>
            <Label>Title Belakang</Label>
            <Input
              name="title_belakang"
              value={formData.title_belakang}
              onChange={handleChange}
            />
          </div>

          {/* ✅ Status Sekretaris Dosen (Dropdown) */}
          <div>
            <Label>Apakah Sekretaris Dosen?</Label>
            <select
              name="is_sekdos"
              value={formData.is_sekdos.toString()}
              onChange={handleChange}
              className="w-full border p-2"
            >
              <option value="false">Tidak</option>
              <option value="true">Ya</option>
            </select>
          </div>

          {/* ✅ Submit Button */}
          <div className="col-span-3 flex justify-end mt-4">
            <Button type="submit" className="bg-primary hover:bg-primary/90">
              {initialData ? "Simpan Perubahan" : "Tambah Dosen"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default DosenForm;
