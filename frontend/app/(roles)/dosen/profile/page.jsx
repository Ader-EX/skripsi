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

  // Form data now includes all fields required by the model.
  const [formData, setFormData] = useState({
    nama: "",
    nidn: "",
    nip: "", // This holds nim_nip (read-only)
    nomorKtp: "",
    tanggalLahir: "",
    progdiId: "",
    statusDosen: "",
    jabatan: "",
    titleDepan: "",
    titleBelakang: "",
    email: "",
    password: "",
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
        nama: data.nama || "",
        nidn: data.nidn || "",
        nip: data.user?.nim_nip || "",
        nomorKtp: data.nomor_ktp || "",
        tanggalLahir: data.tanggal_lahir ? formatDate(data.tanggal_lahir) : "",
        progdiId: data.progdi_id || "",
        statusDosen: data.status_dosen || "",
        jabatan: data.jabatan || "",
        titleDepan: data.title_depan || "",
        titleBelakang: data.title_belakang || "",
        email: data.email || "",
      }));
    } catch (err) {
      setError(err.message);
      console.error("Error fetching user data:", err);
    } finally {
      setLoading(false);
    }
  };

  // Converts date to "YYYY-MM-DD" if not already in that format.
  const formatDate = (dateString) => {
    if (dateString.includes("-")) return dateString;
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

      // Build update payload matching the model:
      const updateData = {
        nim_nip: formData.nip, // required for user update (read-only field)
        nama: formData.nama,
        nidn: formData.nidn,
        nomor_ktp: formData.nomorKtp,
        tanggal_lahir: formData.tanggalLahir, // expecting YYYY-MM-DD format
        progdi_id: formData.progdiId,
        status_dosen: formData.statusDosen,
        jabatan: formData.jabatan,
        title_depan: formData.titleDepan,
        title_belakang: formData.titleBelakang,
        email: formData.email,
      };

      // Include password only if the user provided a new one.
      if (formData.password.trim() !== "") {
        updateData.password = formData.password;
      }

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
                    value={formData.nama || ""}
                    onChange={handleChange}
                    placeholder="Nama Lengkap"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nidn">NIDN</Label>
                  <Input
                    id="nidn"
                    value={formData.nidn || ""}
                    onChange={handleChange}
                    placeholder="NIDN"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nip">NIM/NIP (Tidak bisa diubah)</Label>
                  <Input
                    id="nip"
                    value={formData.nip || ""}
                    readOnly
                    placeholder="NIM/NIP (tidak dapat diubah)"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    value={formData.email || ""}
                    onChange={handleChange}
                    placeholder="Email"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Change Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password || ""}
                    onChange={handleChange}
                    placeholder="Kosongkan jika tidak mau diubah..."
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="nomorKtp">Nomor KTP</Label>
                  <Input
                    id="nomorKtp"
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
                    value={formData.tanggalLahir || ""}
                    onChange={handleChange}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="jabatan">Jabatan</Label>
                  <Input
                    id="jabatan"
                    value={formData.jabatan || ""}
                    onChange={handleChange}
                    placeholder="Jabatan"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="titleDepan">Gelar Depan</Label>
                  <Input
                    id="titleDepan"
                    value={formData.titleDepan || ""}
                    onChange={handleChange}
                    placeholder="Gelar Depan"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="titleBelakang">Gelar Belakang</Label>
                  <Input
                    id="titleBelakang"
                    value={formData.titleBelakang || ""}
                    onChange={handleChange}
                    placeholder="Gelar Belakang"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="statusDosen">Status Dosen</Label>
                  <Select
                    value={formData.statusDosen || ""}
                    onValueChange={(value) =>
                      handleSelectChange(value, "statusDosen")
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
                <Button type="submit">Simpan</Button>
              </div>
            </section>
          </form>
        </Card>
      </div>
    </div>
  );
};

export default DosenProfile;
