"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Building2, Plus, Pencil, Trash2, Filter } from "lucide-react";

const RuanganManagement = () => {
  const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [ruangan, setRuangan] = useState([]);
  const [filters, setFilters] = useState({
    jenis: "",
    gedung: "",
    group_code: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isEdit, setIsEdit] = useState(false);
  const [currentRuangan, setCurrentRuangan] = useState({
    kode_ruangan: "",
    nama_ruang: "",
    tipe_ruangan: "",
    jenis_ruang: "",
    kapasitas: 0,
    gedung: "",
    group_code: "",
    alamat: "",
  });

  // Enums
  const gedungOptions = ["KHD", "DS", "Other"];
  const groupCodeOptions = [
    "KHD2",
    "KHD3",
    "KHD4",
    "DS2",
    "DS3",
    "DS4",
    "Other",
  ];
  const jenisRuangOptions = ["P", "M", "L", "B", "V"];

  const fetchRuangan = async () => {
    try {
      let url = `${BASE_URL}/ruangan`;
      const queryParams = new URLSearchParams();

      if (filters.jenis) queryParams.append("jenis", filters.jenis);
      if (filters.gedung) queryParams.append("gedung", filters.gedung);
      if (filters.group_code)
        queryParams.append("group_code", filters.group_code);
      queryParams.append("page", page);
      queryParams.append("page_size", pageSize);

      if (queryParams.toString()) {
        url += `?${queryParams.toString()}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setRuangan(data.data);
      setTotal(data.total);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching ruangan:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuangan();
  }, [filters, page, pageSize]);

  const handleSelectChange = (value, field) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  const handlePageSizeChange = (newPageSize) => {
    setPageSize(newPageSize);
    setPage(1); // Reset to first page when page size changes
  };

  const handleDelete = async (kode_ruangan) => {
    try {
      const response = await fetch(`${BASE_URL}/ruangan/${kode_ruangan}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setRuangan((prev) =>
          prev.filter((room) => room.kode_ruangan !== kode_ruangan)
        );
      } else {
        console.error("Failed to delete ruangan");
      }
    } catch (error) {
      console.error("Error deleting ruangan:", error);
    }
  };

  const handleEdit = (room) => {
    setCurrentRuangan(room);
    setIsEdit(true);
    setIsDialogOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const method = isEdit ? "PUT" : "POST";
    const url = isEdit
      ? `${BASE_URL}/ruangan/${currentRuangan.kode_ruangan}`
      : `${BASE_URL}/ruangan`;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(currentRuangan),
      });

      if (response.ok) {
        fetchRuangan();
        setIsDialogOpen(false);
        setIsEdit(false);
        setCurrentRuangan({
          kode_ruangan: "",
          nama_ruang: "",
          tipe_ruangan: "",
          jenis_ruang: "",
          kapasitas: 0,
          gedung: "",
          group_code: "",
          alamat: "",
        });
      } else {
        console.error("Failed to save ruangan");
      }
    } catch (error) {
      console.error("Error saving ruangan:", error);
    }
  };

  return (
    <div className="flex w-full ">
      <Card className="flex w-full flex-col">
        <CardHeader className="bg-primary/5">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Building2 className="h-6 w-6 text-primary" />
              <span>Manajemen Ruangan</span>
            </div>
            <Button
              onClick={() => {
                setIsEdit(false);
                setCurrentRuangan({
                  kode_ruangan: "",
                  nama_ruang: "",
                  tipe_ruangan: "",
                  jenis_ruang: "",
                  kapasitas: 0,
                  gedung: "",
                  group_code: "",
                  alamat: "",
                });
                setIsDialogOpen(true);
              }}
              className="bg-primary hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              Tambah Ruangan
            </Button>
          </CardTitle>
        </CardHeader>

        <CardContent>
          {/* Filters */}
          <div className="mb-6 grid grid-cols-3 gap-4">
            <div>
              <Label>Jenis Ruangan</Label>
              <Select
                value={filters.jenis || null}
                onValueChange={(value) => handleSelectChange(value, "jenis")}
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih jenis" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  <SelectItem value="Semua">Semua</SelectItem>
                  {jenisRuangOptions.map((jenis) => (
                    <SelectItem key={jenis} value={jenis}>
                      {jenis}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Gedung</Label>
              <Select
                value={filters.gedung || null}
                onValueChange={(value) => handleSelectChange(value, "gedung")}
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih gedung" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  <SelectItem value="Semua">Semua</SelectItem>
                  {gedungOptions.map((gedung) => (
                    <SelectItem key={gedung} value={gedung}>
                      {gedung}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Kode Grup</Label>
              <Select
                value={filters.group_code || null}
                onValueChange={(value) =>
                  handleSelectChange(value, "group_code")
                }
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih grup" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  <SelectItem value="Semua">Semua</SelectItem>
                  {groupCodeOptions.map((code) => (
                    <SelectItem key={code} value={code}>
                      {code}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow className="bg-primary/5">
                  <TableHead>Kode</TableHead>
                  <TableHead>Nama</TableHead>
                  <TableHead>Tipe</TableHead>
                  <TableHead>Jenis</TableHead>
                  <TableHead>Kapasitas</TableHead>
                  <TableHead>Gedung</TableHead>
                  <TableHead>Grup</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center h-32">
                      <div className="flex items-center justify-center">
                        Loading...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  ruangan.map((room) => (
                    <TableRow key={room.id}>
                      <TableCell className="font-medium">
                        {room.kode_ruangan}
                      </TableCell>
                      <TableCell>{room.nama_ruang}</TableCell>
                      <TableCell>{room.tipe_ruangan}</TableCell>
                      <TableCell>{room.jenis_ruang}</TableCell>
                      <TableCell>{room.kapasitas}</TableCell>
                      <TableCell>{room.gedung}</TableCell>
                      <TableCell>{room.group_code}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 text-blue-500 hover:text-blue-600"
                            onClick={() => handleEdit(room)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-600"
                            onClick={() => handleDelete(room.kode_ruangan)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          <div className="flex justify-between items-center mt-4">
            <div>
              <Label>Page Size</Label>
              <Select
                value={pageSize}
                onValueChange={(value) => handlePageSizeChange(Number(value))}
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Select page size" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {[10, 20, 50].map((size) => (
                    <SelectItem key={size} value={size}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="mx-2">
                Page {page} of {Math.ceil(total / pageSize)}
              </span>
              <Button
                onClick={() => handlePageChange(page + 1)}
                disabled={page * pageSize >= total}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add/Edit Ruangan Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Edit Ruangan" : "Tambah Ruangan Baru"}
            </DialogTitle>
          </DialogHeader>
          <form className="grid gap-4 py-4" onSubmit={handleSave}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="kode_ruangan">Kode Ruangan</Label>
                <Input
                  id="kode_ruangan"
                  value={currentRuangan.kode_ruangan}
                  onChange={(e) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      kode_ruangan: e.target.value,
                    }))
                  }
                  disabled={isEdit}
                />
              </div>
              <div>
                <Label htmlFor="nama_ruang">Nama Ruangan</Label>
                <Input
                  id="nama_ruang"
                  value={currentRuangan.nama_ruang}
                  onChange={(e) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      nama_ruang: e.target.value,
                    }))
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="tipe_ruangan">Tipe</Label>
                <Select
                  value={currentRuangan.tipe_ruangan}
                  onValueChange={(value) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      tipe_ruangan: value,
                    }))
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih tipe" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="P">P</SelectItem>
                    <SelectItem value="T">T</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="jenis_ruang">Jenis</Label>
                <Select
                  value={currentRuangan.jenis_ruang}
                  onValueChange={(value) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      jenis_ruang: value,
                    }))
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih jenis" />
                  </SelectTrigger>
                  <SelectContent>
                    {jenisRuangOptions.map((jenis) => (
                      <SelectItem key={jenis} value={jenis}>
                        {jenis}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="kapasitas">Kapasitas</Label>
                <Input
                  id="kapasitas"
                  type="number"
                  value={currentRuangan.kapasitas}
                  onChange={(e) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      kapasitas: e.target.value,
                    }))
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="gedung">Gedung</Label>
                <Select
                  value={currentRuangan.gedung}
                  onValueChange={(value) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      gedung: value,
                    }))
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih gedung" />
                  </SelectTrigger>
                  <SelectContent>
                    {gedungOptions.map((gedung) => (
                      <SelectItem key={gedung} value={gedung}>
                        {gedung}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="group_code">Kode Grup</Label>
                <Select
                  value={currentRuangan.group_code}
                  onValueChange={(value) =>
                    setCurrentRuangan((prev) => ({
                      ...prev,
                      group_code: value,
                    }))
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih grup" />
                  </SelectTrigger>
                  <SelectContent>
                    {groupCodeOptions.map((code) => (
                      <SelectItem key={code} value={code}>
                        {code}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="alamat">Alamat</Label>
              <Input
                id="alamat"
                value={currentRuangan.alamat}
                onChange={(e) =>
                  setCurrentRuangan((prev) => ({
                    ...prev,
                    alamat: e.target.value,
                  }))
                }
              />
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
              >
                Batal
              </Button>
              <Button type="submit" className="bg-primary hover:bg-primary/90">
                Simpan
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RuanganManagement;
