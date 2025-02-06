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
import { Book, Plus, Pencil, Trash2, Filter, Search } from "lucide-react";

const MataKuliahManagement = () => {
  const [matakuliah, setMatakuliah] = useState([]);
  const [programStudi, setProgramStudi] = useState([]);
  const [filters, setFilters] = useState({
    semester: "",
    kurikulum: "",
    status_mk: "",
    have_kelas_besar: "",
    search: "",
  });
  const [searchInput, setSearchInput] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isEdit, setIsEdit] = useState(false);
  const [currentMataKuliah, setCurrentMataKuliah] = useState({
    kodemk: "",
    namamk: "",
    sks: 0,
    smt: 0,
    kurikulum: "",
    status_mk: "",
    have_kelas_besar: false,
    program_studi_id: "",
  });

  // Constants
  const semesterOptions = ["Semua", 1, 2, 3, 4, 5, 6, 7, 8];
  const statusMKOptions = ["Semua", "A", "N"]; // Active/Non-active
  const haveKelasBesarOptions = ["Semua", "true", "false"];

  const fetchMataKuliah = async () => {
    try {
      let url = `${process.env.NEXT_PUBLIC_API_URL}/matakuliah`;
      const queryParams = new URLSearchParams();

      if (filters.semester && filters.semester !== "Semua")
        queryParams.append("semester", filters.semester);
      if (filters.kurikulum) queryParams.append("kurikulum", filters.kurikulum);
      if (filters.status_mk && filters.status_mk !== "Semua")
        queryParams.append("status_mk", filters.status_mk);
      if (filters.have_kelas_besar && filters.have_kelas_besar !== "Semua")
        queryParams.append("have_kelas_besar", filters.have_kelas_besar);
      if (filters.search) queryParams.append("search", filters.search);
      queryParams.append("page", page);
      queryParams.append("page_size", pageSize);

      if (queryParams.toString()) {
        url += `?${queryParams.toString()}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setMatakuliah(data.data);
      setTotal(data.total);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching matakuliah:", error);
      setLoading(false);
    }
  };

  const fetchMataKuliahDetails = async (kodemk) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/matakuliah/${kodemk}`
      );
      const data = await response.json();
      setCurrentMataKuliah(data);
      setIsEdit(true);
      setIsDialogOpen(true);
    } catch (error) {
      console.error("Error fetching matakuliah details:", error);
    }
  };

  useEffect(() => {
    fetchMataKuliah();
    // Fetch program studi list
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/program-studi`)
      .then((res) => res.json())
      .then((data) => setProgramStudi(data))
      .catch((error) => console.error("Error fetching program studi:", error));
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

  const handleSearchClick = () => {
    setFilters((prev) => ({
      ...prev,
      search: searchInput,
    }));
  };

  const handleDelete = async (kodemk) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/matakuliah/${kodemk}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        setMatakuliah((prev) => prev.filter((mk) => mk.kodemk !== kodemk));
      } else {
        console.error("Failed to delete matakuliah");
      }
    } catch (error) {
      console.error("Error deleting matakuliah:", error);
    }
  };

  const handleDialogClose = () => {
    setIsDialogOpen(false);
    setIsEdit(false);
    setCurrentMataKuliah({
      kodemk: "",
      namamk: "",
      sks: 0,
      smt: 0,
      kurikulum: "",
      status_mk: "",
      have_kelas_besar: false,
      program_studi_id: "",
    });
  };

  const handleInputChange = (event) => {
    setFilters((prev) => ({
      ...prev,
      search: event.target.value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const method = isEdit ? "PUT" : "POST";
    const url = isEdit
      ? `${process.env.NEXT_PUBLIC_API_URL}/matakuliah/${currentMataKuliah.kodemk}`
      : `${process.env.NEXT_PUBLIC_API_URL}/matakuliah`;

    try {
      const response = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(currentMataKuliah),
      });

      if (response.ok) {
        fetchMataKuliah();
        handleDialogClose();
      } else {
        console.error("Failed to save matakuliah");
      }
    } catch (error) {
      console.error("Error saving matakuliah:", error);
    }
  };

  return (
    <div className="flex w-full">
      <Card className="flex flex-col w-full">
        <CardHeader className="bg-primary/5">
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Book className="h-6 w-6 text-primary" />
              <span>Manajemen Mata Kuliah</span>
            </div>
            <Button
              onClick={() => setIsDialogOpen(true)}
              className="bg-primary hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              Tambah Mata Kuliah
            </Button>
          </CardTitle>
        </CardHeader>

        <CardContent>
          {/* Filters */}
          <div className="col-span-2 flex gap-2 mb-4">
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Cari Kode atau Nama Mata Kuliah"
              className="bg-white"
            />
            <Button
              className="bg-secondary hover:bg-secondary/90"
              onClick={handleSearchClick}
            >
              <Search className="h-4 w-4" />
            </Button>
          </div>
          <div className="mb-6 grid grid-cols-4 gap-4">
            <div>
              <Label>Semester</Label>
              <Select
                value={filters.semester || ""}
                onValueChange={(value) => handleSelectChange(value, "semester")}
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih semester" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {semesterOptions.map((semester) => (
                    <SelectItem key={semester} value={semester}>
                      {semester}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Kurikulum</Label>
              <Input
                value={filters.kurikulum}
                onChange={(e) =>
                  handleSelectChange(e.target.value, "kurikulum")
                }
                placeholder="Masukkan kurikulum"
                className="bg-white"
              />
            </div>

            <div>
              <Label>Status MK</Label>
              <Select
                value={filters.status_mk || ""}
                onValueChange={(value) =>
                  handleSelectChange(value, "status_mk")
                }
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih status MK" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {statusMKOptions.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Have Kelas Besar</Label>
              <Select
                value={filters.have_kelas_besar || ""}
                onValueChange={(value) =>
                  handleSelectChange(value, "have_kelas_besar")
                }
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Pilih kelas besar" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {haveKelasBesarOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
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
                  <TableHead>SKS</TableHead>
                  <TableHead>Semester</TableHead>
                  <TableHead>Kurikulum</TableHead>
                  <TableHead>Status MK</TableHead>
                  <TableHead>Kelas Besar</TableHead>
                  <TableHead>Program Studi</TableHead>
                  <TableHead className="text-right">Aksi</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center h-32">
                      <div className="flex items-center justify-center">
                        Loading...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  matakuliah.map((mk) => (
                    <TableRow key={mk.kodemk}>
                      <TableCell className="font-medium">{mk.kodemk}</TableCell>
                      <TableCell>{mk.namamk}</TableCell>
                      <TableCell>{mk.sks}</TableCell>
                      <TableCell>{mk.smt}</TableCell>
                      <TableCell>{mk.kurikulum}</TableCell>
                      <TableCell>{mk.status_mk}</TableCell>
                      <TableCell>
                        {mk.have_kelas_besar ? "Yes" : "No"}
                      </TableCell>
                      <TableCell>{mk.program_studi_name}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 text-blue-500 hover:text-blue-600"
                            onClick={() => fetchMataKuliahDetails(mk.kodemk)}
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 text-red-500 hover:text-red-600"
                            onClick={() => handleDelete(mk.kodemk)}
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
                value={pageSize.toString()}
                onValueChange={(value) => handlePageSizeChange(Number(value))}
              >
                <SelectTrigger className="bg-white">
                  <SelectValue placeholder="Select page size" />
                </SelectTrigger>
                <SelectContent className="bg-white">
                  {[10, 20, 50].map((size) => (
                    <SelectItem key={size} value={size.toString()}>
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

      {/* Add/Edit Mata Kuliah Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>
              {isEdit ? "Edit Mata Kuliah" : "Tambah Mata Kuliah Baru"}
            </DialogTitle>
          </DialogHeader>
          <form className="grid gap-4 py-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="kodemk">Kode MK</Label>
                <Input
                  id="kodemk"
                  value={currentMataKuliah.kodemk}
                  onChange={(e) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      kodemk: e.target.value,
                    })
                  }
                  disabled={isEdit}
                />
              </div>
              <div>
                <Label htmlFor="namamk">Nama MK</Label>
                <Input
                  id="namamk"
                  value={currentMataKuliah.namamk}
                  onChange={(e) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      namamk: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="sks">SKS</Label>
                <Input
                  id="sks"
                  type="number"
                  value={currentMataKuliah.sks}
                  onChange={(e) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      sks: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label htmlFor="smt">Semester</Label>
                <Select
                  value={currentMataKuliah.smt.toString()}
                  onValueChange={(value) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      smt: Number(value),
                    })
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih semester" />
                  </SelectTrigger>
                  <SelectContent>
                    {semesterOptions.map((semester) => (
                      <SelectItem key={semester} value={semester.toString()}>
                        {semester}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="status_mk">Status MK</Label>
                <Select
                  value={currentMataKuliah.status_mk}
                  onValueChange={(value) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      status_mk: value,
                    })
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih status MK" />
                  </SelectTrigger>
                  <SelectContent>
                    {statusMKOptions.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="have_kelas_besar">Have Kelas Besar</Label>
                <Select
                  value={currentMataKuliah.have_kelas_besar.toString()}
                  onValueChange={(value) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      have_kelas_besar: value === "true",
                    })
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih kelas besar" />
                  </SelectTrigger>
                  <SelectContent>
                    {haveKelasBesarOptions.map((option) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="program_studi_id">Program Studi</Label>
                <Select
                  value={currentMataKuliah.program_studi_id.toString()}
                  onValueChange={(value) =>
                    setCurrentMataKuliah({
                      ...currentMataKuliah,
                      program_studi_id: Number(value),
                    })
                  }
                >
                  <SelectTrigger className="bg-white">
                    <SelectValue placeholder="Pilih program studi" />
                  </SelectTrigger>
                  <SelectContent>
                    {programStudi.map((ps) => (
                      <SelectItem key={ps.id} value={ps.id.toString()}>
                        {ps.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={handleDialogClose}
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

export default MataKuliahManagement;
