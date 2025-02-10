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

const API_URL = `${process.env.NEXT_PUBLIC_API_URL}/mahasiswa`;
const POST_USER_API = `${process.env.NEXT_PUBLIC_API_URL}/user/user-only`;
const USER_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/user/users/`;
const PROGRAM_STUDI_API_URL = `${process.env.NEXT_PUBLIC_API_URL}/program-studi/`;

const MahasiswaForm = ({ isOpen, onClose, initialData, onSubmit }) => {
  const [programStudiList, setProgramStudiList] = useState([]);
  // If editing, use existing data. Otherwise, use default empty values.
  const [formData, setFormData] = useState(
    initialData || {
      user: { fullname: "", email: "", password: "" },
      tahun_masuk: 2024,
      semester: 1,
      sks_diambil: 0,
      tgl_lahir: "",
      kota_lahir: "",
      jenis_kelamin: "L",
      kewarganegaraan: "",
      alamat: "",
      kode_pos: "",
      hp: "",
      nama_ayah: "",
      nama_ibu: "",
      pekerjaan_ayah: "",
      pekerjaan_ibu: "",
      status_kawin: false,
      program_studi_id: "",
    }
  );

  // Update formData when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      setFormData({
        user: { fullname: "", email: "", password: "" },
        tahun_masuk: 2024,
        semester: 1,
        sks_diambil: 0,
        tgl_lahir: "",
        kota_lahir: "",
        jenis_kelamin: "L",
        kewarganegaraan: "",
        alamat: "",
        kode_pos: "",
        hp: "",
        nama_ayah: "",
        nama_ibu: "",
        pekerjaan_ayah: "",
        pekerjaan_ibu: "",
        status_kawin: false,
        program_studi_id: "",
      });
    }
  }, [initialData]);

  useEffect(() => {
    const fetchProgramStudi = async () => {
      try {
        const response = await fetch(PROGRAM_STUDI_API_URL);
        if (!response.ok) throw new Error("Failed to fetch program studi");
        const data = await response.json();
        setProgramStudiList(data);
      } catch (error) {
        console.error("Error fetching program studi:", error);
      }
    };

    fetchProgramStudi();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    if (name === "fullname" || name === "email" || name === "password") {
      setFormData((prev) => ({
        ...prev,
        user: {
          ...prev.user,
          [name]: value,
        },
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: type === "checkbox" ? checked : value,
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      console.log("Submitting form data:", formData);

      let userId = formData.user_id;

      // **Check if user already exists before creating a new one**
      const userExistsResponse = await fetch(
        `${USER_API_URL}/check-exists?email=${formData.user.email}`
      );
      if (userExistsResponse.ok) {
        console.log("USER THELAH ADA:");
        const existingUser = await userExistsResponse.json();
        console.log(existingUser);
        userId = existingUser.id; // ✅ Assign existing user ID
      } else {
        console.log("USER DOESNT EXIST");
        // **Create a new user if it doesn't exist**
        const userResponse = await fetch(POST_USER_API, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            fullname: formData.user.fullname,
            email: formData.user.email,
            password: formData.user.password,
            role: "mahasiswa",
          }),
        });

        if (!userResponse.ok) toast.error("Failed to create user");
        const userData = await userResponse.json();
        if (
          userData.statusCode == 400 ||
          userData.statusCode == 409 ||
          userData.statusCode == 500
        ) {
          console.log("ERRROR");
          toast.error(userData.detail);
          return;
        }
        console.log(userData);
        userId = userData.id;
      }

      // **Prepare Mahasiswa Data**
      const formattedData = {
        user_id: userId,
        program_studi_id: parseInt(formData.program_studi_id, 10),
        tahun_masuk: formData.tahun_masuk,
        semester: formData.semester,
        sks_diambil: formData.sks_diambil,
        tgl_lahir: formData.tgl_lahir || null,
        kota_lahir: formData.kota_lahir || null,
        jenis_kelamin: formData.jenis_kelamin,
        kewarganegaraan: formData.kewarganegaraan || null,
        alamat: formData.alamat || null,
        kode_pos: formData.kode_pos ? parseInt(formData.kode_pos, 10) : null,
        hp: formData.hp,
      };

      // **Use PUT if user exists, otherwise use POST**
      const method = userExistsResponse.ok ? "PUT" : "POST";
      const url = userExistsResponse.ok ? `${API_URL}/${userId}` : `${API_URL}`;

      console.log(formattedData);

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formattedData),
      });

      console.log(response.json());

      if (!response.ok) {
        toast.error(
          `Error ${method === "POST" ? "adding" : "updating"} mahasiswa: ${
            response.detail
          }`
        );
      }
      toast.success(
        initialData
          ? "Mahasiswa berhasil diupdate"
          : "Mahasiswa berhasil ditambahkan"
      );
      onSubmit();
      onClose();
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Mahasiswa" : "Tambah Mahasiswa"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="gap-4 grid grid-cols-3">
          <div className="col-span-3">
            <Label>Nama</Label>
            <Input
              name="fullname"
              value={formData.user?.fullname || ""}
              onChange={handleChange}
              required
            />
          </div>
          <div className="col-span-3">
            <Label>Email</Label>
            <Input
              name="email"
              type="email"
              value={formData.user?.email || ""}
              onChange={handleChange}
              required
            />
          </div>

          {!initialData && (
            <div className="col-span-3">
              <Label>Password</Label>
              <Input
                autoComplete="new-password"
                name="password"
                type="password"
                required
              />
            </div>
          )}

          <div>
            <Label>Tahun Masuk</Label>
            <Input
              name="tahun_masuk"
              type="number"
              value={formData.tahun_masuk || ""}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Semester</Label>
            <Input
              name="semester"
              type="number"
              value={formData.semester || ""}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>SKS Diambil</Label>
            <Input
              name="sks_diambil"
              type="number"
              value={formData.sks_diambil || ""}
              onChange={handleChange}
              required
            />
          </div>

          <div>
            <Label>Tanggal Lahir</Label>
            <Input
              name="tgl_lahir"
              type="date"
              value={formData.tgl_lahir || ""}
              onChange={handleChange}
            />
          </div>

          <div>
            <Label>Kota Lahir</Label>
            <Input
              name="kota_lahir"
              value={formData.kota_lahir || ""}
              onChange={handleChange}
            />
          </div>

          <div>
            <Label>Jenis Kelamin</Label>
            <select
              name="jenis_kelamin"
              value={formData.jenis_kelamin || ""}
              onChange={handleChange}
              className="w-full border p-2"
            >
              <option value="L">Laki-Laki</option>
              <option value="P">Perempuan</option>
            </select>
          </div>

          <div>
            <Label>Kewarganegaraan</Label>
            <Input
              name="kewarganegaraan"
              value={formData.kewarganegaraan || ""}
              onChange={handleChange}
            />
          </div>

          <div>
            <Label>Alamat</Label>
            <Input
              name="alamat"
              value={formData.alamat || ""}
              onChange={handleChange}
            />
          </div>

          <div>
            <Label>Kode Pos</Label>
            <Input
              name="kode_pos"
              type="number"
              value={formData.kode_pos || ""}
              onChange={handleChange}
            />
          </div>

          <div>
            <Label>No HP</Label>
            <Input
              name="hp"
              value={formData.hp || ""}
              onChange={handleChange}
              required
            />
          </div>

          <div className="col-span-2">
            <Label>Program Studi</Label>
            <select
              name="program_studi_id"
              value={formData.program_studi_id || ""}
              onChange={handleChange}
              className="w-full border p-2"
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

          <div className="col-span-2">
            <Button type="submit" className="w-full">
              {initialData ? "Simpan Perubahan" : "Tambah Mahasiswa"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default MahasiswaForm;
