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
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const DosenProfile = () => {
  const router = useRouter();
  const [userId, setUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");

  const [formData, setFormData] = useState({
    nama: "",
    nidn: "",
    nip: "",
    nomorKtp: "",
    tanggalLahir: "",
    progdiId: "",
    ijinMengajar: "true",
    jabatan: "",
    titleDepan: "",
    titleBelakang: "",
    isSekdos: "false",
    isDosenKb: "false",
    pegawai_id: 0,
    jabatan_id: 0,
  });

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const token = Cookies.get("access_token");
      if (!token) {
        router.push("/");
        return;
      }

      const payload = decodeToken(token);
      if (!payload?.sub) throw new Error("Invalid token payload");

      const response = await fetch(`${BASE_URL}/dosen/${payload.role_id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch user details");
      const data = await response.json();

      setUserId(payload.role_id);
      setFormData((prev) => ({
        ...prev,
        nama: data.user?.nim_nip || "",
        nidn: data.nidn || "",
        nip: data.user?.nim_nip || "",
        nomorKtp: data.nomor_ktp || "",
        tanggalLahir: data.tanggal_lahir ? formatDate(data.tanggal_lahir) : "",
        progdiId: data.progdi_id || "",
        ijinMengajar: data.ijin_mengajar ? "true" : "false",
        jabatan: data.jabatan || "",
        titleDepan: data.title_depan || "",
        titleBelakang: data.title_belakang || "",
        isSekdos: data.is_sekdos ? "true" : "false",
        pegawai_id: data.pegawai_id || 0,
        jabatan_id: data.jabatan_id || 0,
      }));
    } catch (err) {
      setError(err.message);
      console.error("Error fetching user data:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const [day, month, year] = dateString.split("/");
    return `${year}-${month}-${day}`;
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
      if (!userId) throw new Error("User ID not found");

      const updateData = {
        nomor_ktp: formData.nomorKtp,
        email: formData.email,
        progdi_id: formData.progdiId,
        tanggal_lahir: formData.tanggalLahir,
        title_depan: formData.titleDepan,
        title_belakang: formData.titleBelakang,
        ijin_mengajar: formData.ijinMengajar === "true",
        jabatan: formData.jabatan,
        is_sekdos: formData.isSekdos === "true",
      };

      const response = await fetch(`${BASE_URL}/dosen/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${Cookies.get("access_token")}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update profile");
      }

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
      <div className="max-w-7xl space-y-4">
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
                Dosen Profile
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="nama">Nama Lengkap</Label>
                  <Input
                    id="nama"
                    required
                    value={formData.nama || ""}
                    onChange={handleChange}
                    placeholder="Nama Lengkap"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nidn">NIDN</Label>
                  <Input
                    id="nidn"
                    required
                    value={formData.nidn || ""}
                    onChange={handleChange}
                    placeholder="NIDN"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nip">NIP</Label>
                  <Input
                    id="nip"
                    value={formData.nip || ""}
                    onChange={handleChange}
                    placeholder="NIP"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nomorKtp">Nomor KTP</Label>
                  <Input
                    id="nomorKtp"
                    required
                    value={formData.nomorKtp || ""}
                    onChange={handleChange}
                    placeholder="Nomor KTP"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tanggalLahir">Tanggal Lahir</Label>
                  <Input
                    type="date"
                    id="tanggalLahir"
                    required
                    value={formData.tanggalLahir || ""}
                    onChange={handleChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="jabatan">Jabatan</Label>
                  <Input
                    id="jabatan"
                    required
                    value={formData.jabatan || ""}
                    onChange={handleChange}
                    placeholder="Jabatan"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="titleDepan">Gelar Depan</Label>
                  <Input
                    id="titleDepan"
                    required
                    value={formData.titleDepan || ""}
                    onChange={handleChange}
                    placeholder="Gelar Depan"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="titleBelakang">Gelar Belakang</Label>
                  <Input
                    id="titleBelakang"
                    required
                    value={formData.titleBelakang || ""}
                    onChange={handleChange}
                    placeholder="Gelar Belakang"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="ijinMengajar">Izin Mengajar</Label>
                  <Select
                    required
                    value={formData.ijinMengajar || ""}
                    onValueChange={(value) =>
                      handleSelectChange(value, "ijinMengajar")
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Pilih izin mengajar" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="true">Ya</SelectItem>
                      <SelectItem value="false">Tidak</SelectItem>
                    </SelectContent>
                  </Select>
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

export default DosenProfile;
