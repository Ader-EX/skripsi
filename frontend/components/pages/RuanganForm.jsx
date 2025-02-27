import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const RuanganForm = ({ isOpen, onClose, isEdit, ruangan, fetchRuangan }) => {
  const [formData, setFormData] = useState({
    kode_ruangan: "",
    nama_ruang: "",
    tipe_ruangan: "T",
    kapasitas: 0,
    gedung: "",
    group_code: "",
    alamat: "",
  });

  const [errors, setErrors] = useState({});
  const token = Cookies.get("access_token");

  useEffect(() => {
    if (isEdit && ruangan) {
      setFormData(ruangan);
    } else {
      setFormData({
        kode_ruangan: "",
        nama_ruang: "",
        tipe_ruangan: "T",
        kapasitas: "",
        gedung: "",
        group_code: "",
        alamat: "",
      });
    }
  }, [isEdit, ruangan]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSelectChange = (value, field) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const validateForm = () => {
    let newErrors = {};

    if (!formData.kode_ruangan.trim()) newErrors.kode_ruangan = "Wajib diisi";
    if (!formData.nama_ruang.trim()) newErrors.nama_ruang = "Wajib diisi";
    if (!formData.kapasitas || formData.kapasitas <= 0)
      newErrors.kapasitas = "Wajib diisi dan harus lebih dari 0";
    if (!formData.gedung.trim()) newErrors.gedung = "Wajib diisi";
    if (!formData.group_code.trim()) newErrors.group_code = "Wajib diisi";
    if (!formData.alamat.trim()) newErrors.alamat = "Wajib diisi";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      toast.error("Harap isi semua bidang yang wajib diisi.");
      return;
    }

    try {
      const method = isEdit ? "PUT" : "POST";
      const url = isEdit
        ? `${API_URL}/ruangan/${formData.id}`
        : `${API_URL}/ruangan`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });
      if (!response.ok) throw new Error("Gagal menyimpan ruangan");

      toast.success(
        isEdit ? "Ruangan berhasil diperbarui" : "Ruangan berhasil ditambahkan"
      );
      fetchRuangan();
      onClose();
    } catch (error) {
      console.error("Error:", error);
      toast.error("Terjadi kesalahan saat menyimpan ruangan");
    }
  };

  const handleDelete = async () => {
    if (!isEdit) return;

    try {
      const response = await fetch(`${API_URL}/ruangan/${formData.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) throw new Error("Gagal menghapus ruangan");

      toast.success("Ruangan berhasil dihapus");
      fetchRuangan();
      onClose();
    } catch (error) {
      console.error("Error:", error);
      toast.error("Terjadi kesalahan saat menghapus ruangan");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit Ruangan" : "Tambah Ruangan"}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div>
            <Label htmlFor="kode_ruangan">Kode Ruangan</Label>
            <Input
              id="kode_ruangan"
              name="kode_ruangan"
              value={formData.kode_ruangan || ""}
              onChange={handleChange}
              placeholder="Kode Ruangan"
              disabled={isEdit}
              required
            />
            {errors.kode_ruangan && (
              <p className="text-red-500 text-sm">{errors.kode_ruangan}</p>
            )}
          </div>

          <div>
            <Label htmlFor="nama_ruang">Nama Ruangan</Label>
            <Input
              id="nama_ruang"
              name="nama_ruang"
              value={formData.nama_ruang}
              onChange={handleChange}
              placeholder="Nama Ruangan"
              required
            />
            {errors.nama_ruang && (
              <p className="text-red-500 text-sm">{errors.nama_ruang}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="tipe_ruangan">Tipe Ruangan</Label>
              <Select
                value={formData.tipe_ruangan}
                onValueChange={(value) =>
                  handleSelectChange(value, "tipe_ruangan")
                }
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Pilih tipe ruangan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="P">Praktikum</SelectItem>
                  <SelectItem value="T">Teori</SelectItem>
                  <SelectItem value="S">Spesial</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="kapasitas">Kapasitas</Label>
              <Input
                id="kapasitas"
                name="kapasitas"
                type="number"
                value={formData.kapasitas}
                onChange={handleChange}
                placeholder="Kapasitas"
                required
              />
              {errors.kapasitas && (
                <p className="text-red-500 text-sm">{errors.kapasitas}</p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="gedung">Grup Gedung</Label>
              <Select
                value={formData.group_code}
                onValueChange={(value) =>
                  handleSelectChange(value, "group_code")
                }
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Pilih gedung" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="KHD2">KHD2</SelectItem>
                  <SelectItem value="KHD3">KHD3</SelectItem>
                  <SelectItem value="KHD4">KHD4</SelectItem>
                  <SelectItem value="DS2">DS2</SelectItem>
                  <SelectItem value="DS3">DS3</SelectItem>
                  <SelectItem value="DS4">DS4</SelectItem>

                  <SelectItem value="OTH">Other</SelectItem>
                </SelectContent>
              </Select>
              {errors.gedung && (
                <p className="text-red-500 text-sm">{errors.gedung}</p>
              )}
            </div>
            <div>
              <Label htmlFor="gedung">Gedung</Label>
              <Select
                value={formData.gedung}
                onValueChange={(value) => handleSelectChange(value, "gedung")}
                required
              >
                <SelectTrigger>
                  <SelectValue placeholder="Pilih gedung" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="KHD">KHD</SelectItem>
                  <SelectItem value="DS">DS</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="alamat">Alamat</Label>
            <Input
              id="alamat"
              name="alamat"
              value={formData.alamat}
              onChange={handleChange}
              placeholder="Alamat"
              required
            />
            {errors.alamat && (
              <p className="text-red-500 text-sm">{errors.alamat}</p>
            )}
          </div>
        </div>

        <DialogFooter>
          {isEdit && (
            <Button variant="destructive" onClick={handleDelete}>
              Hapus
            </Button>
          )}
          <Button variant="outline" onClick={onClose}>
            Batal
          </Button>
          <Button onClick={handleSubmit}>
            {isEdit ? "Simpan Perubahan" : "Tambah"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default RuanganForm;
