"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Book, Plus } from "lucide-react";
import MataKuliahTable from "./MataKuliahTable";
import MataKuliahForm from "./MataKuliahForm";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

const MataKuliahManagement = () => {
  const [matakuliah, setMatakuliah] = useState([]);
  const [programStudi, setProgramStudi] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    semester: "",
    kurikulum: "",
    status_mk: "",
    have_kelas_besar: "",
    search: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentMataKuliah, setCurrentMataKuliah] = useState(null);
  const token = Cookies.get("access_token");
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  useEffect(() => {
    fetchMataKuliah();
    fetchProgramStudi();
  }, [filters, page, pageSize]);

  const fetchMataKuliah = async () => {
    try {
      setOverlayText("Memuat data mata kuliah...");
      setIsActive(true);
      let url = `${API_URL}/matakuliah?page=${page}&page_size=${pageSize}`;
      const queryParams = new URLSearchParams();

      // Only append semester if it's a valid number and not "Semua"
      if (filters.semester && filters.semester !== "Semua") {
        queryParams.append("semester", filters.semester);
      }
      if (filters.kurikulum) queryParams.append("kurikulum", filters.kurikulum);
      if (filters.status_mk && filters.status_mk !== "Semua")
        queryParams.append("status_mk", filters.status_mk);
      if (filters.have_kelas_besar && filters.have_kelas_besar !== "Semua")
        queryParams.append("have_kelas_besar", filters.have_kelas_besar);
      if (filters.search) queryParams.append("search", filters.search);

      if (queryParams.toString()) {
        url += `&${queryParams.toString()}`;
      }

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setMatakuliah(data.data);
      setTotal(data.total);
    } catch (error) {
      console.error("Error fetching matakuliah:", error);
    } finally {
      setIsActive(false);
    }
  };

  const fetchProgramStudi = async () => {
    try {
      setOverlayText("Memuat data...");
      setIsActive(true);
      const response = await fetch(`${API_URL}/program-studi`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setProgramStudi(data);
    } catch (error) {
      console.error("Error fetching program studi:", error);
    } finally {
      setIsActive(false);
    }
  };

  const handleDeleteConfirm = async (kodemk) => {
    try {
      const response = await fetch(`${API_URL}/matakuliah/${kodemk}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success("MataKuliah deleted successfully");
        fetchMataKuliah();
      } else {
        throw new Error("Failed to delete MataKuliah");
      }
    } catch (error) {
      console.error("Error deleting MataKuliah:", error);
      toast.error("Error deleting MataKuliah");
    }
  };

  const handleOpenForm = (matakuliah = null) => {
    setCurrentMataKuliah(matakuliah);
    setIsEdit(!!matakuliah);
    setIsDialogOpen(true);
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
              onClick={() => handleOpenForm(null)}
              className="bg-primary hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              Tambah Mata Kuliah
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Replace MataKuliahTable with your table component */}
          {/* Pass necessary props */}
          <MataKuliahTable
            matakuliah={matakuliah}
            total={total}
            filters={filters}
            setFilters={setFilters}
            page={page}
            setPage={setPage}
            pageSize={pageSize}
            setPageSize={setPageSize}
            handleDelete={handleDeleteConfirm}
            handleEdit={handleOpenForm}
            fetchMataKuliah={fetchMataKuliah}
          />
        </CardContent>
      </Card>

      <MataKuliahForm
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        isEdit={isEdit}
        matakuliah={currentMataKuliah}
        fetchMataKuliah={fetchMataKuliah}
        programStudi={programStudi}
      />
    </div>
  );
};

export default MataKuliahManagement;
