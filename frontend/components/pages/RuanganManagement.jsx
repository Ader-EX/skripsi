"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Building2, Plus } from "lucide-react";
import RuanganTable from "./RuanganTable";
import RuanganForm from "./RuanganForm";
import toast from "react-hot-toast";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const RuanganManagement = () => {
  const [ruangan, setRuangan] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    jenis: "",
    gedung: "",
    group_code: "",
  });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [currentRuangan, setCurrentRuangan] = useState(null);
  const token = Cookies.get("access_token");

  // Get loading overlay functions from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  useEffect(() => {
    fetchRuangan();
  }, [filters, page, pageSize]);

  const fetchRuangan = async () => {
    try {
      // Show loading overlay with custom text
      setOverlayText("Memuat data ruangan...");
      setIsActive(true);
      let url = `${API_URL}/ruangan?page=${page}&page_size=${pageSize}`;
      const queryParams = new URLSearchParams(filters);
      url += `&${queryParams.toString()}`;

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setRuangan(data.data);
      setTotal(data.total);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching ruangan:", error);
      setLoading(false);
    } finally {
      // Hide the loading overlay regardless of success/failure
      setIsActive(false);
    }
  };

  const handleEdit = (room) => {
    setCurrentRuangan(room);
    setIsEdit(true);
    setIsDialogOpen(true);
  };

  const handleDelete = async (kode_ruangan) => {
    try {
      const response = await fetch(`${API_URL}/ruangan/${kode_ruangan}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        toast.success("Ruangan berhasil dihapus");
        fetchRuangan();
      } else {
        toast.error("Failed to delete ruangan");
      }
    } catch (error) {
      toast.error("Error deleting ruangan:", error);
    }
  };

  return (
    <div className="flex w-full">
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
                setCurrentRuangan(null);
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
          <RuanganTable
            ruangan={ruangan}
            total={total}
            loading={loading}
            filters={filters}
            setFilters={setFilters}
            page={page}
            setPage={setPage}
            pageSize={pageSize}
            setPageSize={setPageSize}
            handleEdit={handleEdit}
            handleDelete={handleDelete}
          />
        </CardContent>
      </Card>

      <RuanganForm
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        isEdit={isEdit}
        ruangan={currentRuangan}
        fetchRuangan={fetchRuangan}
      />
    </div>
  );
};

export default RuanganManagement;
