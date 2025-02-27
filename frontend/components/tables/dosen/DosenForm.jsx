"use client";
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import toast from "react-hot-toast";
import Cookies from "js-cookie";

const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi`;

// Helper: Convert API date ("dd/mm/yyyy") to input date ("yyyy-mm-dd")
const convertToInputDateFormat = (dateStr) => {
  if (!dateStr) return "";
  const parts = dateStr.split("/");
  if (parts.length !== 3) return dateStr;
  const [day, month, year] = parts;
  return `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
};

const DosenForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const convertDateFormat = (dateStr) => {
    if (!dateStr) return "";
    const [year, month, day] = dateStr.split("-");
    return `${day}/${month}/${year}`;
  };
  const [programStudiList, setProgramStudiList] = useState([]);
  const [formData, setFormData] = useState(
    initialData || {
      nama: "",
      email: "",
      password: "",
      nim_nip: "",
      pegawai_id: "",
      nidn: "",
      nomor_ktp: "",
      tanggal_lahir: "",
      progdi_id: "",
      ijin_mengajar: true,
      status_dosen: "",
      jabatan: "",
      title_depan: "",
      title_belakang: "",
    }
  );
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (initialData) {
      setFormData({
        email: initialData.email || "",
        password: initialData.password || "",
        nim_nip: initialData.user?.nim_nip || "",
        pegawai_id: initialData.pegawai_id || "",
        nidn: initialData.nidn || "",
        nomor_ktp: initialData.nomor_ktp || "",
        nama: initialData.nama || "",
        tanggal_lahir: initialData.tanggal_lahir
          ? convertToInputDateFormat(initialData.tanggal_lahir)
          : "",
        progdi_id: initialData.progdi_id || "",
        ijin_mengajar:
          initialData.ijin_mengajar !== undefined
            ? initialData.ijin_mengajar
            : true,
        // Note: We use initialData.status_dosen (or empty string) for statusDosen
        status_dosen: initialData.status_dosen || "",
        jabatan: initialData.jabatan || "",
        title_depan: initialData.title_depan || "",
        title_belakang: initialData.title_belakang || "",
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
        statusDosen: "",
        jabatan: "",
        title_depan: "",
        title_belakang: "",

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
  }, [token]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSelectChange = (value, field) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formattedData = {
      ...formData,
      tanggal_lahir: formData.tanggal_lahir
        ? convertDateFormat(formData.tanggal_lahir)
        : "",
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
          {/* Nama */}
          <div className="col-span-3">
            <Label htmlFor="nama">Nama</Label>
            <Input
              id="nama"
              name="nama"
              value={formData.nama}
              onChange={handleChange}
              required
            />
          </div>

          {/* Email */}
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          {/* NIM/NIP */}
          <div>
            <Label htmlFor="nim_nip">NIM/NIP</Label>
            <Input
              id="nim_nip"
              name="nim_nip"
              value={formData.nim_nip}
              onChange={handleChange}
              required
            />
          </div>

          {/* Password (Only show for new dosen) */}
          {!initialData && (
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
          )}

          {/* Pegawai ID */}
          <div>
            <Label htmlFor="pegawai_id">Pegawai ID</Label>
            <Input
              id="pegawai_id"
              name="pegawai_id"
              type="number"
              value={formData.pegawai_id}
              onChange={handleChange}
            />
          </div>

          {/* NIDN */}
          <div>
            <Label htmlFor="nidn">NIDN</Label>
            <Input
              id="nidn"
              name="nidn"
              value={formData.nidn}
              onChange={handleChange}
            />
          </div>

          {/* Nomor KTP */}
          <div>
            <Label htmlFor="nomor_ktp">Nomor KTP</Label>
            <Input
              id="nomor_ktp"
              name="nomor_ktp"
              value={formData.nomor_ktp}
              onChange={handleChange}
            />
          </div>

          {/* Tanggal Lahir */}
          <div>
            <Label htmlFor="tanggal_lahir">Tanggal Lahir</Label>
            <Input
              id="tanggal_lahir"
              name="tanggal_lahir"
              type="date"
              value={formData.tanggal_lahir}
              onChange={handleChange}
              required
            />
          </div>

          {/* Program Studi */}
          <div>
            <Label htmlFor="progdi_id">Program Studi</Label>
            <Select
              required
              value={formData.progdi_id}
              onValueChange={(value) => handleSelectChange(value, "progdi_id")}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Pilih Program Studi" />
              </SelectTrigger>
              <SelectContent>
                {programStudiList.map((prog) => (
                  <SelectItem key={prog.id} value={prog.id.toString()}>
                    {prog.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Ijin Mengajar */}
          <div>
            <Label htmlFor="ijin_mengajar">Izin Mengajar</Label>
            <Select
              value={formData.ijin_mengajar.toString()}
              onValueChange={(value) =>
                handleSelectChange(value === "true", "ijin_mengajar")
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Pilih Izin Mengajar" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">Ya</SelectItem>
                <SelectItem value="false">Tidak</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Status Dosen */}
          <div>
            <Label htmlFor="status_dosen">Status Dosen</Label>
            <Select
              value={formData.status_dosen || ""}
              onValueChange={(value) =>
                handleSelectChange(value, "status_dosen")
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Pilih status dosen" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tetap">Tetap</SelectItem>
                <SelectItem value="tidak tetap">Tidak Tetap</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Jabatan */}
          <div>
            <Label htmlFor="jabatan">Jabatan</Label>
            <Input
              id="jabatan"
              name="jabatan"
              value={formData.jabatan}
              onChange={handleChange}
            />
          </div>

          {/* Jabatan ID */}

          {/* Title Depan */}
          <div>
            <Label htmlFor="title_depan">Title Depan</Label>
            <Input
              id="title_depan"
              name="title_depan"
              value={formData.title_depan}
              onChange={handleChange}
            />
          </div>

          {/* Title Belakang */}
          <div>
            <Label htmlFor="title_belakang">Title Belakang</Label>
            <Input
              id="title_belakang"
              name="title_belakang"
              value={formData.title_belakang}
              onChange={handleChange}
            />
          </div>

          {/* Dialog Footer: Submit Button */}
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
