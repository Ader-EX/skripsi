import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import toast from "react-hot-toast";
import Cookies from "js-cookie";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/academic-period`;

const AcademicPeriodForm = ({ isOpen, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState(
    initialData || {
      tahun_ajaran: "",
      semester: "",
      start_date: "",
      end_date: "",
      is_active: false, // New academic period should default to inactive
    }
  );

  const token = Cookies.get("access_token");

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? e.target.checked : value,
    }));
  };

  const handleCheckboxChange = (checked) => {
    setFormData((prev) => ({
      ...prev,
      is_active: checked,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (new Date(formData.start_date) >= new Date(formData.end_date)) {
      alert("Tanggal mulai harus lebih awal dari tanggal berakhir.");
      return;
    }

    const method = initialData ? "PUT" : "POST";
    const url = initialData ? `${API_URL}/${initialData.id}` : API_URL;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        onSubmit(); // Refresh academic periods
        onClose(); // Close form
      } else {
        const errorData = await response.json();
        toast.error(`Gagal menyimpan data: ${errorData.detail}`);
      }
    } catch (error) {
      toast.error("Error saving academic period:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Periode Akademik" : "Tambah Periode Akademik"}
          </DialogTitle>
        </DialogHeader>
        <form className="grid gap-4 py-4" onSubmit={handleSubmit}>
          <Label>Tahun Ajaran</Label>
          <Input
            name="tahun_ajaran"
            value={formData.tahun_ajaran}
            onChange={handleChange}
            required
          />

          <Label>Semester</Label>
          <Input
            type="number"
            name="semester"
            value={formData.semester}
            onChange={handleChange}
            required
          />

          <Label>Tanggal Mulai</Label>
          <Input
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            required
          />

          <Label>Tanggal Berakhir</Label>
          <Input
            type="date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            required
          />

          <div className="flex items-center gap-2">
            <Checkbox
              id="is_active"
              checked={formData.is_active}
              onCheckedChange={handleCheckboxChange}
            />
            <Label htmlFor="is_active">Jadikan Periode Aktif</Label>
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose}>
              Batal
            </Button>
            <Button type="submit" className="bg-primary hover:bg-primary/90">
              Simpan
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AcademicPeriodForm;
