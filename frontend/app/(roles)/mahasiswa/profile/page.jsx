"use client";

import React, { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import Cookies from "js-cookie";
import { decodeToken } from "@/utils/decoder";
import toast from "react-hot-toast";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MahasiswaProfile = () => {
  const [userId, setUserId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");

  const [formData, setFormData] = useState({
    nama: "",
    tgl_lahir: "",
    kota_lahir: "",
    jenis_kelamin: "L", // Underlying value "L" by default
    alamat: "",
    kode_pos: "",
    hp: "",
    email: "",
    kewarganegaraan: "",
    nama_ayah: "",
    nama_ibu: "",
    pekerjaan_ayah: "",
    pekerjaan_ibu: "",
    status_kawin: 0,
  });
  const token = Cookies.get("access_token");

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = Cookies.get("access_token");
      if (!token) {
        throw new Error("No access token found");
      }

      const payload = decodeToken(token);
      if (!payload?.sub) {
        throw new Error("Invalid token payload");
      }

      const response = await fetch(`${BASE_URL}/mahasiswa/${payload.role_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        throw new Error("Failed to fetch user details");
      }

      const data = await response.json();
      setUserId(data.id);
      setFormData((prev) => ({
        ...prev,
        ...data,
        tgl_lahir: data.tgl_lahir || "",
        kota_lahir: data.kota_lahir || "",
        // Set jenis_kelamin to underlying value; default to "L" if not provided.
        jenis_kelamin: data.jenis_kelamin || "L",
        kode_pos: data.kode_pos || "",
        nama_ayah: data.nama_ayah || "",
        nama_ibu: data.nama_ibu || "",
        pekerjaan_ayah: data.pekerjaan_ayah || "",
        pekerjaan_ibu: data.pekerjaan_ibu || "",
        status_kawin: data.status_kawin || 0,
      }));
    } catch (err) {
      setError(err.message);
      console.error("Error fetching user data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  const handleSelectChange = (value, field) => {
    if (field === "status_kawin") {
      setFormData((prev) => ({
        ...prev,
        [field]: value === "Belum Kawin" ? 0 : 1,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage("");

    try {
      if (!userId) {
        throw new Error("User ID not found");
      }

      const response = await fetch(`${BASE_URL}/mahasiswa/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to update profile");
      }

      const data = await response.json();
      setSuccessMessage("Profile updated successfully");
      toast.success("Profile updated successfully");
    } catch (err) {
      setError(err.message);
      console.error("Error updating profile:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full p-4">
      <div className="max-w-7xl  space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMessage && (
          <Alert>
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}

        <Card className="w-full shadow-sm">
          <form onSubmit={handleSubmit} className="divide-y divide-gray-200">
            {/* Basic Information Section */}
            <section className="p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                Basic Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="nama" className="text-gray-700">
                    Nama Lengkap
                  </Label>
                  <Input
                    id="nama"
                    value={formData.nama}
                    onChange={handleChange}
                    placeholder="Masukkan nama lengkap"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tgl_lahir" className="text-gray-700">
                    Tanggal Lahir
                  </Label>
                  <Input
                    type="date"
                    id="tgl_lahir"
                    value={formData.tgl_lahir}
                    onChange={handleChange}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="kota_lahir" className="text-gray-700">
                    Kota Lahir
                  </Label>
                  <Input
                    id="kota_lahir"
                    value={formData.kota_lahir}
                    onChange={handleChange}
                    placeholder="Masukkan kota lahir"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="jenis_kelamin" className="text-gray-700">
                    Jenis Kelamin
                  </Label>
                  <Select
                    className=""
                    value={formData.jenis_kelamin}
                    onValueChange={(value) =>
                      handleSelectChange(value, "jenis_kelamin")
                    }
                  >
                    <SelectTrigger className="w-full ">
                      <SelectValue placeholder="Pilih jenis kelamin" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="L">Laki-laki</SelectItem>
                      <SelectItem value="P">Perempuan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="kewarganegaraan" className="text-gray-700">
                    Kewarganegaraan
                  </Label>
                  <Input
                    id="kewarganegaraan"
                    value={formData.kewarganegaraan}
                    onChange={handleChange}
                    placeholder="Masukkan kewarganegaraan"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status_kawin" className="text-gray-700">
                    Status Perkawinan
                  </Label>
                  <Select
                    value={
                      formData.status_kawin === 0
                        ? "Belum Kawin"
                        : "Sudah Kawin"
                    }
                    onValueChange={(value) =>
                      handleSelectChange(value, "status_kawin")
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Pilih status perkawinan" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="Belum Kawin">Belum Kawin</SelectItem>
                      <SelectItem value="Sudah Kawin">Sudah Kawin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </section>

            {/* Contact Information Section */}
            <section className="p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                Contact Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="alamat" className="text-gray-700">
                    Alamat
                  </Label>
                  <Input
                    id="alamat"
                    value={formData.alamat}
                    onChange={handleChange}
                    placeholder="Masukkan alamat lengkap"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="kode_pos" className="text-gray-700">
                    Kode Pos
                  </Label>
                  <Input
                    type="number"
                    id="kode_pos"
                    value={formData.kode_pos}
                    onChange={handleChange}
                    placeholder="Masukkan kode pos"
                    pattern="[0-9]*"
                    maxLength={5}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hp" className="text-gray-700">
                    Nomor HP
                  </Label>
                  <Input
                    id="hp"
                    value={formData.hp}
                    onChange={handleChange}
                    placeholder="Masukkan nomor HP"
                    type="tel"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-gray-700">
                    Email
                  </Label>
                  <Input
                    id="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Masukkan email"
                    type="email"
                    className="w-full bg-gray-50"
                  />
                </div>
              </div>
            </section>

            {/* Form Actions */}
            <section className="p-6 bg-gray-50">
              <div className="flex justify-end space-x-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => window.history.back()}
                >
                  Cancel
                </Button>
                <Button type="submit">Save Changes</Button>
              </div>
            </section>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default MahasiswaProfile;
