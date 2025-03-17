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
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa`;
const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi/`;

const MahasiswaForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const token = Cookies.get("access_token");

  const [programStudiList, setProgramStudiList] = useState([]);
  const [formData, setFormData] = useState(
    initialData || {
      nim_nip: "",
      password: "",
      nama: "",
      tahun_masuk: new Date().getFullYear(),
      semester: 1,
      sks_diambil: 0,
      tgl_lahir: "",
      kota_lahir: "",
      jenis_kelamin: "L",
      kewarganegaraan: "Indonesia",
      alamat: "",
      kode_pos: "",
      hp: "",
      program_studi_id: "",
    }
  );

  useEffect(() => {
    if (initialData) {
      setFormData({
        ...initialData,
        program_studi_id: initialData.program_studi_id?.toString(),
        kode_pos: initialData.kode_pos?.toString() || "",
      });
    } else {
      setFormData({
        nim_nip: "",
        password: "",
        nama: "",
        tahun_masuk: new Date().getFullYear(),
        semester: 1,
        sks_diambil: 0,
        tgl_lahir: "",
        kota_lahir: "",
        jenis_kelamin: "L",
        kewarganegaraan: "Indonesia",
        alamat: "",
        kode_pos: "",
        hp: "",
        program_studi_id: "",
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
        toast.error("Gagal mengambil data program studi.");
        console.error("Error fetching program studi:", error);
      }
    };

    fetchProgramStudi();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const payload = {
        ...formData,
        program_studi_id: parseInt(formData.program_studi_id),
        kode_pos: formData.kode_pos ? parseInt(formData.kode_pos) : null,
        tahun_masuk: parseInt(formData.tahun_masuk),
        semester: parseInt(formData.semester),
        sks_diambil: parseInt(formData.sks_diambil),
      };

      // Remove password if editing and no new password provided
      if (initialData && !payload.password) {
        delete payload.password;
      }

      const method = initialData ? "PUT" : "POST";
      const url = initialData ? `${API_URL}/${initialData.id}` : API_URL;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save mahasiswa");
      }

      toast.success(
        `Mahasiswa berhasil ${initialData ? "diupdate" : "ditambahkan"}`
      );
      onSubmit();
      onClose();
    } catch (error) {
      toast.error(error.message || "Terjadi kesalahan saat menyimpan data.");
      console.error("Error submitting form:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-[900px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Mahasiswa" : "Tambah Mahasiswa"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            {/* Section 1: Basic Info */}
            <div className="col-span-2">
              <Label>NIM/NIP</Label>
              <Input
                name="nim_nip"
                value={formData.nim_nip}
                onChange={handleChange}
                required
              />
            </div>

            {!initialData && (
              <div className="col-span-2">
                <Label>Password</Label>
                <Input
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  required={!initialData}
                />
              </div>
            )}

            <div className="col-span-2">
              <Label>Nama Lengkap</Label>
              <Input
                name="nama"
                value={formData.nama}
                onChange={handleChange}
                required
              />
            </div>

            <div className="col-span-2">
              <Label>Program Studi</Label>
              <select
                name="program_studi_id"
                value={formData.program_studi_id}
                onChange={handleChange}
                className="w-full border p-2 rounded-md"
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

            {/* Section 2: Academic Info */}
            <div>
              <Label>Semester</Label>
              <Input
                name="semester"
                type="number"
                value={formData.semester}
                onChange={handleChange}
                required
                min="1"
              />
            </div>

            <div>
              <Label>Tahun Masuk</Label>
              <Input
                name="tahun_masuk"
                type="number"
                value={formData.tahun_masuk}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <Label>SKS Diambil</Label>
              <Input
                name="sks_diambil"
                type="number"
                value={formData.sks_diambil}
                onChange={handleChange}
                required
                min="0"
              />
            </div>

            <div>
              <Label>Jenis Kelamin</Label>
              <select
                name="jenis_kelamin"
                value={formData.jenis_kelamin}
                onChange={handleChange}
                className="w-full border p-2 rounded-md"
                required
              >
                <option value="L">Laki-laki</option>
                <option value="P">Perempuan</option>
              </select>
            </div>

            {/* Section 3: Personal Info */}
            <div>
              <Label>Tanggal Lahir</Label>
              <Input
                name="tgl_lahir"
                type="date"
                required
                value={formData.tgl_lahir}
                onChange={handleChange}
              />
            </div>

            <div>
              <Label>Kota Lahir</Label>
              <Input
                name="kota_lahir"
                value={formData.kota_lahir}
                onChange={handleChange}
              />
            </div>

            <div>
              <Label>Kewarganegaraan</Label>
              <Input
                name="kewarganegaraan"
                value={formData.kewarganegaraan}
                onChange={handleChange}
              />
            </div>

            <div>
              <Label>No. HP</Label>
              <Input name="hp" value={formData.hp} onChange={handleChange} />
            </div>

            {/* Section 4: Address */}
            <div className="col-span-3">
              <Label>Alamat</Label>
              <Input
                name="alamat"
                value={formData.alamat}
                onChange={handleChange}
              />
            </div>

            <div>
              <Label>Kode Pos</Label>
              <Input
                name="kode_pos"
                value={formData.kode_pos}
                onChange={handleChange}
                type="number"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Batal
            </Button>
            <Button type="submit">
              {initialData ? "Simpan Perubahan" : "Tambah Mahasiswa"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default MahasiswaForm;
