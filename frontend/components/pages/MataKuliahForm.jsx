"use client";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label"; // ✅ Import Label
import toast from "react-hot-toast";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const MataKuliahForm = ({
  isOpen,
  onClose,
  isEdit,
  matakuliah,
  fetchMataKuliah,
  programStudi,
}) => {
  const token = Cookies.get("access_token");

  const [formData, setFormData] = useState({
    kodemk: "",
    namamk: "",
    sks: "",
    smt: "",
    kurikulum: "",
    status_mk: "",
    tipe_mk: "",
    have_kelas_besar: false,
    program_studi_id: "",
  });

  useEffect(() => {
    if (isEdit && matakuliah) {
      setFormData({
        kodemk: matakuliah.kodemk,
        namamk: matakuliah.namamk,
        sks: matakuliah.sks,
        smt: matakuliah.smt,
        kurikulum: matakuliah.kurikulum,
        status_mk: matakuliah.status_mk,
        tipe_mk: matakuliah.tipe_mk,
        have_kelas_besar: matakuliah.have_kelas_besar,
        program_studi_id: matakuliah.program_studi_id,
      });
    } else {
      setFormData({
        kodemk: "",
        namamk: "",
        sks: "",
        smt: "",
        kurikulum: "",
        status_mk: "",
        tipe_mk: "",
        have_kelas_besar: false,
        program_studi_id: "",
      });
    }
  }, [isEdit, matakuliah]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async () => {
    try {
      const method = isEdit ? "PUT" : "POST";
      const url = isEdit
        ? `${API_URL}/matakuliah/${formData.kodemk}`
        : `${API_URL}/matakuliah/`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error("Failed to save MataKuliah");

      toast.success(
        isEdit
          ? "MataKuliah updated successfully"
          : "MataKuliah created successfully"
      );
      fetchMataKuliah();
      onClose();
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error saving MataKuliah");
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit MataKuliah" : "Tambah MataKuliah"}
          </DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div>
            <Label htmlFor="kodemk">Kode Mata Kuliah</Label>
            <Input
              id="kodemk"
              name="kodemk"
              value={formData.kodemk}
              onChange={handleChange}
              placeholder="Kode Mata Kuliah"
              disabled={isEdit}
            />
          </div>

          <div>
            <Label htmlFor="namamk">Nama Mata Kuliah</Label>
            <Input
              id="namamk"
              name="namamk"
              value={formData.namamk}
              onChange={handleChange}
              placeholder="Nama Mata Kuliah"
            />
          </div>

          <div>
            <Label htmlFor="sks">SKS</Label>
            <Input
              id="sks"
              name="sks"
              value={formData.sks}
              onChange={handleChange}
              type="number"
              placeholder="SKS"
            />
          </div>

          <div>
            <Label htmlFor="smt">Semester</Label>
            <Input
              id="smt"
              name="smt"
              value={formData.smt}
              onChange={handleChange}
              type="number"
              placeholder="Semester"
            />
          </div>

          <div>
            <Label htmlFor="kurikulum">Kurikulum</Label>
            <Input
              id="kurikulum"
              name="kurikulum"
              value={formData.kurikulum}
              onChange={handleChange}
              placeholder="Kurikulum"
            />
          </div>

          <div>
            <Label htmlFor="status_mk">Status Mata Kuliah</Label>
            <Select
              name="status_mk"
              value={formData.status_mk}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, status_mk: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="A">Aktif</SelectItem>
                <SelectItem value="N">Nonaktif</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="tipe_mk">Tipe Mata Kuliah</Label>
            <Select
              name="tipe_mk"
              value={formData.tipe_mk}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, tipe_mk: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Tipe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="T">Teori</SelectItem>
                <SelectItem value="P">Praktikum</SelectItem>
                <SelectItem value="S">Spesial</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="program_studi_id">Program Studi</Label>
            <Select
              name="program_studi_id"
              value={formData.program_studi_id}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, program_studi_id: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Pilih Program Studi" />
              </SelectTrigger>
              <SelectContent>
                {programStudi.map((ps) => (
                  <SelectItem key={ps.id} value={ps.id}>
                    {ps.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={onClose} variant="outline">
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

export default MataKuliahForm;
