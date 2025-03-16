"use client";
import React, { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Switch } from "@/components/ui/switch";
import { Pencil, Trash2 } from "lucide-react";
import toast from "react-hot-toast";

import DosenSelectionDialog from "@/components/global/DosenSelectionDialog";
import MatakuliahSelectionDialog from "@/components/global/MatakuliahSelectionDialog";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const EditOpenedClass = () => {
  const router = useRouter();
  const searchParams = window !== "undefined" ? useSearchParams() : null;
  const classId = searchParams ? searchParams.get("id") : null; // Check if it's PUT mode

  const [selectedMataKuliah, setSelectedMataKuliah] = useState(null);
  const [selectedDosen, setSelectedDosen] = useState([]);
  const [kelas, setKelas] = useState(""); // will hold one of A-L
  const [kapasitas, setKapasitas] = useState("");
  const [isMataKuliahDialogOpen, setIsMataKuliahDialogOpen] = useState(false);
  const [isDosenDialogOpen, setIsDosenDialogOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  const token = Cookies.get("access_token");

  useEffect(() => {
    setIsMounted(true);
    if (classId) {
      fetchOpenedClassDetails(classId);
    }
  }, [classId]);

  const fetchOpenedClassDetails = async (id) => {
    try {
      const response = await fetch(`${API_URL}/opened-class/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch opened class details");

      const data = await response.json();
      setSelectedMataKuliah({
        kodemk: data.mata_kuliah_kodemk,
        nama: data.nama,
        tipe_mk: data.tipe_mk,
        have_kelas_besar: data.have_kelas_besar,
      });
      setKelas(data.kelas);
      setKapasitas(data.kapasitas);

      setSelectedDosen(
        data.dosens.map((dosen) => ({
          id: dosen.pegawai_id,
          nama: dosen.nama,
          isDosenBesar: dosen.is_dosen_besar || false,
          usedPreference: dosen.used_preference || false,
        }))
      );
    } catch (error) {
      console.error("Error fetching opened class:", error);
    }
  };

  const handleMataKuliahSelect = (matakuliah) => {
    setSelectedMataKuliah({
      kodemk: matakuliah.kodemk,
      nama: matakuliah.namamk,
      tipe_mk: matakuliah.tipe_mk,
      have_kelas_besar: matakuliah.have_kelas_besar,
    });
  };

  const handleDosenSelect = (dosen) => {
    setSelectedDosen((prev) => [
      ...prev,
      {
        id: dosen.id,
        nama: dosen.nama,
        isDosenBesar: false,
        usedPreference: false,
      },
    ]);
  };

  const handleDosenBesarToggle = (dosenId) => {
    setSelectedDosen((prev) =>
      prev.map((dosen) =>
        dosen.id === dosenId
          ? { ...dosen, isDosenBesar: !dosen.isDosenBesar }
          : { ...dosen, isDosenBesar: false }
      )
    );
  };

  const handleUsedPreferenceToggle = (dosenId) => {
    setSelectedDosen((prev) =>
      prev.map((dosen) =>
        dosen.id === dosenId
          ? { ...dosen, usedPreference: true }
          : { ...dosen, usedPreference: false }
      )
    );
  };

  const handleRemoveDosen = (dosenId) => {
    setSelectedDosen((prev) => prev.filter((d) => d.id !== dosenId));
  };

  const handleSubmit = async () => {
    if (
      !selectedMataKuliah ||
      !kelas ||
      !kapasitas ||
      selectedDosen.length === 0
    ) {
      toast.error("Please complete all fields.");
      return;
    }

    try {
      const method = classId ? "PUT" : "POST";
      const url = classId
        ? `${API_URL}/opened-class/${classId}`
        : `${API_URL}/opened-class`;

      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          mata_kuliah_kodemk: selectedMataKuliah.kodemk,
          kelas, // now one of A-L
          kapasitas: parseInt(kapasitas, 10),
          dosens: selectedDosen.map((d) => ({
            id: d.id,
            is_dosen_besar: d.isDosenBesar,
            used_preference: d.usedPreference,
          })),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        toast.error("Kelas gagal disimpan : " + data.detail);
        return;
      }

      toast.success("Kelas disimpan!");
      router.push("/admin/data-manajemen");
    } catch (error) {
      toast.error("Failed to save opened class");
    }
  };

  if (!isMounted) {
    return (
      <div className="flex justify-center items-center h-screen">
        Loading...
      </div>
    );
  }

  // Options for class selection (A-L)
  const classOptions = "ABCDEFGHIJKLMNOPQ".split("");

  return (
    <div className="p-8 flex flex-col w-full gap-6">
      <Card>
        <CardHeader>
          <div
            onClick={() => router.back()}
            className="mb-4 text-blue-500 text-sm cursor-pointer"
          >
            &larr; Kembali ke halaman sebelumnya
          </div>
          <CardTitle className="flex gap-x-2 text-blue-500 items-center">
            <div className="flex gap-x-2 ">
              <Pencil className="w-4 " />
              <h1 className="self-center">Opened Class Editor</h1>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Label>Mata Kuliah</Label>
          <Input
            value={
              selectedMataKuliah
                ? `${selectedMataKuliah.kodemk} - ${selectedMataKuliah.nama}`
                : ""
            }
            placeholder="Select Mata Kuliah"
            readOnly
            onClick={() => setIsMataKuliahDialogOpen(true)}
            className="w-full cursor-pointer"
          />

          <Label>Kelas</Label>
          <select
            value={kelas}
            onChange={(e) => setKelas(e.target.value)}
            className="w-full mb-4 p-2 border rounded"
          >
            <option value="" disabled>
              Pilih Kelas
            </option>
            {classOptions.map((letter) => (
              <option key={letter} value={letter}>
                {letter}
              </option>
            ))}
          </select>

          <Label>Kapasitas</Label>
          <Input
            type="text"
            value={kapasitas}
            onChange={(e) => setKapasitas(e.target.value)}
            className="w-full mb-4"
          />

          <div className="flex flex-col sm:flex-row w-full justify-between my-4">
            <Label>Dosen Pengampu</Label>
            <Button
              className="mb-2 bg-primary"
              onClick={() => {
                setIsDosenDialogOpen(true);
              }}
            >
              Pilih Dosen
            </Button>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nama Dosen</TableHead>
                {selectedMataKuliah?.tipe_mk === "T" && (
                  <TableHead>Dosen Besar</TableHead>
                )}
                <TableHead>Gunakan Preferensi?</TableHead>
                <TableHead>Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {selectedDosen.map((dosen) => (
                <TableRow key={dosen.id}>
                  <TableCell>{dosen.nama}</TableCell>
                  {selectedMataKuliah?.tipe_mk === "T" && (
                    <TableCell>
                      <Switch
                        checked={dosen.isDosenBesar}
                        onCheckedChange={() => handleDosenBesarToggle(dosen.id)}
                      />
                    </TableCell>
                  )}
                  <TableCell>
                    <Switch
                      checked={dosen.usedPreference}
                      onCheckedChange={() =>
                        handleUsedPreferenceToggle(dosen.id)
                      }
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      size="icon"
                      variant="outline"
                      onClick={() => handleRemoveDosen(dosen.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Button onClick={handleSubmit} className="mt-6 bg-primary">
        {classId ? "Update Opened Class" : "Create Opened Class"}
      </Button>

      <MatakuliahSelectionDialog
        isOpen={isMataKuliahDialogOpen}
        onClose={() => setIsMataKuliahDialogOpen(false)}
        onSelect={handleMataKuliahSelect}
      />

      <DosenSelectionDialog
        isOpen={isDosenDialogOpen}
        onClose={() => setIsDosenDialogOpen(false)}
        onSelect={handleDosenSelect}
      />
    </div>
  );
};

export default EditOpenedClass;
