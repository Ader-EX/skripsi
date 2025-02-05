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

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MahasiswaProfile = () => {
  const [userId, setUserId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const jobOptions = [
    "PNS",
    "Wiraswasta",
    "Petani",
    "Buruh",
    "Pegawai Swasta",
    "Guru/Dosen",
    "Dokter",
    "Polisi/TNI",
    "Lainnya",
  ];
  const [formData, setFormData] = useState({
    nama: "",
    tglLahir: "",
    kotaLahir: "",
    jenisKelamin: "Laki-laki",
    alamat: "",
    kodePos: "",
    hp: "",
    email: "",
    kewarganegaraan: "",
    namaAyah: "",
    namaIbu: "",
    pekerjaanAyah: "",
    pekerjaanIbu: "",
    statusKawin: "Belum Kawin",
  });

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

      const encodedEmail = encodeURIComponent(payload.sub);
      const response = await fetch(
        `${BASE_URL}/user/details?email=${encodedEmail}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch user details");
      }

      const data = await response.json();
      setUserId(data.id);
      setFormData((prev) => ({
        ...prev,
        ...data,
        tglLahir: data.tgl_lahir || "",
        kotaLahir: data.kota_lahir || "",
        jenisKelamin: data.jenis_kelamin || "Laki-laki",
        kodePos: data.kode_pos || "",
        namaAyah: data.nama_ayah || "",
        namaIbu: data.nama_ibu || "",
        pekerjaanAyah: data.pekerjaan_ayah || "",
        pekerjaanIbu: data.pekerjaan_ibu || "",
        statusKawin: data.status_kawin || "Belum Kawin",
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
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
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
      console.log("Profile updated:", data);
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
                  <Label htmlFor="tglLahir" className="text-gray-700">
                    Tanggal Lahir
                  </Label>
                  <Input
                    type="date"
                    id="tglLahir"
                    value={formData.tglLahir}
                    onChange={handleChange}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="kotaLahir" className="text-gray-700">
                    Kota Lahir
                  </Label>
                  <Input
                    id="kotaLahir"
                    value={formData.kotaLahir}
                    onChange={handleChange}
                    placeholder="Masukkan kota lahir"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="jenisKelamin" className="text-gray-700">
                    Jenis Kelamin
                  </Label>
                  <Select
                    className=""
                    value={formData.jenisKelamin}
                    onValueChange={(value) =>
                      handleSelectChange(value, "jenisKelamin")
                    }
                  >
                    <SelectTrigger className="w-full ">
                      <SelectValue placeholder="Pilih jenis kelamin" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="Laki-laki">Laki-laki</SelectItem>
                      <SelectItem value="Perempuan">Perempuan</SelectItem>
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
                  <Label htmlFor="statusKawin" className="text-gray-700">
                    Status Perkawinan
                  </Label>
                  <Select
                    value={formData.statusKawin}
                    onValueChange={(value) =>
                      handleSelectChange(value, "statusKawin")
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Pilih status perkawinan" />
                    </SelectTrigger>
                    <SelectContent className="bg-white">
                      <SelectItem value="Belum Kawin">Belum Kawin</SelectItem>
                      <SelectItem value="Kawin">Kawin</SelectItem>
                      <SelectItem value="Cerai Hidup">Cerai Hidup</SelectItem>
                      <SelectItem value="Cerai Mati">Cerai Mati</SelectItem>
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
                  <Label htmlFor="kodePos" className="text-gray-700">
                    Kode Pos
                  </Label>
                  <Input
                    type="text"
                    id="kodePos"
                    value={formData.kodePos}
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
                    disabled
                    className="w-full bg-gray-50"
                  />
                </div>
              </div>
            </section>

            {/* Parent Information Section */}
            <section className="p-6">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">
                Parent Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="namaAyah" className="text-gray-700">
                    Nama Ayah
                  </Label>
                  <Input
                    id="namaAyah"
                    value={formData.namaAyah}
                    onChange={handleChange}
                    placeholder="Masukkan nama ayah"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="namaIbu" className="text-gray-700">
                    Nama Ibu
                  </Label>
                  <Input
                    id="namaIbu"
                    value={formData.namaIbu}
                    onChange={handleChange}
                    placeholder="Masukkan nama ibu"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pekerjaanAyah" className="text-gray-700">
                    Pekerjaan Ayah
                  </Label>
                  <Input
                    id="pekerjaanAyah"
                    value={formData.pekerjaanAyah}
                    onChange={handleChange}
                    placeholder="Masukkan pekerjaan ayah"
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="pekerjaanIbu" className="text-gray-700">
                    Pekerjaan Ibu
                  </Label>
                  <Input
                    id="pekerjaanIbu"
                    value={formData.pekerjaanIbu}
                    onChange={handleChange}
                    placeholder="Masukkan pekerjaan ibu"
                    className="w-full"
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
