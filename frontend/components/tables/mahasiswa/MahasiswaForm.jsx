import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}`;

const MahasiswaForm = ({ isOpen, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState(
    initialData || {
      fullname: "",
      email: "",
      password: "",
      tahun_masuk: 2024,
      semester: 1,
      sks_diambil: 0,
      program_studi_id: "",
    }
  );

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      // Step 1: Create User
      const userResponse = await fetch(`${API_URL}/user/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fullname: formData.fullname,
          email: formData.email,
          password: formData.password,
          role: "mahasiswa",
        }),
      });

      if (!userResponse.ok) {
        throw new Error("Failed to create user.");
      }

      const userData = await userResponse.json();

      // Step 2: Create Mahasiswa
      const mahasiswaResponse = await fetch(`${API_URL}/mahasiswa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userData.id,
          tahun_masuk: formData.tahun_masuk,
          semester: formData.semester,
          sks_diambil: formData.sks_diambil,
          nama: formData.fullname,
          email: formData.email,
          program_studi_id: formData.program_studi_id,
        }),
      });

      if (!mahasiswaResponse.ok) {
        throw new Error("Failed to create mahasiswa.");
      }

      onSubmit();
      onClose();
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Tambah Mahasiswa</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <Label>Nama</Label>
          <Input name="fullname" onChange={handleChange} required />
          <Label>Email</Label>
          <Input name="email" onChange={handleChange} required />
          <Label>Password</Label>
          <Input
            name="password"
            type="password"
            onChange={handleChange}
            required
          />
          <Button type="submit">Simpan</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default MahasiswaForm;
