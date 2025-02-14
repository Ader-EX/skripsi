"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PersonStandingIcon, Plus, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import DosenTable from "./DosenTable";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

const DosenManagement = () => {
  const [dosenList, setDosenList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [totalPages, setTotalPages] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);

  const [searchInput, setSearchInput] = useState(""); // Stores user input
  const [search, setSearch] = useState(""); // Stores actual query when button is clicked

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  useEffect(() => {
    fetchDosen();
  }, [page, limit, search]); // ✅ Fetch only when search button is clicked

  const fetchDosen = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
      });

      if (search) {
        params.append("search", search);
      }

      const response = await fetch(
        `http://localhost:8000/dosen/get-all?${params}`
      );
      if (!response.ok) throw new Error("Failed to fetch dosen");

      const data = await response.json();
      setDosenList(data.data);
      setTotalPages(data.total_pages);
      setTotalRecords(data.total_records);
    } catch (error) {
      console.error("Error fetching dosen:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchClick = () => {
    setSearch(searchInput); // ✅ Set search query only when clicking "Search"
    setPage(1); // Reset to first page when searching
  };

  const handleEdit = (data) => {
    console.log("Edit:", data);
  };

  const handleDeleteClick = (id) => {
    setDeleteId(id);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deleteId) return;
    try {
      const response = await fetch(`http://localhost:8000/dosen/${deleteId}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to delete dosen");
      fetchDosen();
    } catch (error) {
      console.error("Error deleting dosen:", error);
    } finally {
      setDeleteModalOpen(false);
      setDeleteId(null);
    }
  };

  return (
    <Card className="flex flex-col w-full">
      <CardHeader className="bg-primary/5">
        <CardTitle className="flex items-center justify-between">
          <span>Manajemen Dosen</span>
          <Button className="bg-primary hover:bg-primary/90">
            <Plus className="mr-2 h-4 w-4" />
            Tambah Dosen
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="col-span-3">
            <Label>Pencarian</Label>
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Cari berdasarkan nama atau email..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)} // ✅ Updates input only
              />
              <Button onClick={handleSearchClick} className="bg-primary">
                <Search />
              </Button>
            </div>
          </div>

          <div>
            <Label>Per page</Label>
            <Select
              value={limit.toString()}
              onValueChange={(value) => setLimit(Number(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 20, 30, 50].map((value) => (
                  <SelectItem key={value} value={value.toString()}>
                    {value}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="text-center py-4">Loading...</div>
        ) : (
          <DosenTable
            dosenList={dosenList}
            onEdit={handleEdit}
            onDelete={handleDeleteClick}
          />
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-500">
            Showing {totalRecords === 0 ? 0 : (page - 1) * limit + 1} to{" "}
            {Math.min(page * limit, totalRecords)} of {totalRecords}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage((p) => p + 1)}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Konfirmasi Hapus</DialogTitle>
            </DialogHeader>
            <p>Apakah Anda yakin ingin menghapus Dosen ini?</p>
            <DialogFooter className="flex justify-end gap-2 mt-4">
              <Button
                variant="outline"
                onClick={() => setDeleteModalOpen(false)}
              >
                Batal
              </Button>
              <Button variant="destructive" onClick={handleConfirmDelete}>
                Hapus
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default DosenManagement;
