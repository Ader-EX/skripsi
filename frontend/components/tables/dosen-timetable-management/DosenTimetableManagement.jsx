"use client";
import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2 } from "lucide-react";
import DosenTimetableManagementTable from "./DosenTimetableManagementTable";
import Cookies from "js-cookie";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const DosenTimeTableManagement = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [dosenList, setDosenList] = useState([]);
  const [selectedDosen, setSelectedDosen] = useState(null);
  const [timetableList, setTimetableList] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const token = Cookies.get("access_token");

  // Loading overlay controls from context
  const { setIsActive, setOverlayText } = useLoadingOverlay();

  // When a dosen is selected, fetch its timetable
  useEffect(() => {
    if (selectedDosen?.id) {
      fetchTimetables();
    }
  }, [selectedDosen]);

  const fetchDosen = async () => {
    try {
      setIsLoading(true);
      setError(null);
      // Show overlay while fetching dosen data
      setOverlayText("Memuat data dosen...");
      setIsActive(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/dosen/get-dosen/names?page=1&limit=10&filter=${searchTerm}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) {
        throw new Error("Failed to fetch dosen data");
      }
      const data = await response.json();
      setDosenList(data.data || []);
    } catch (error) {
      console.error("Error fetching dosen:", error);
      setError("Failed to fetch dosen list");
      setDosenList([]);
    } finally {
      setIsLoading(false);
      setIsActive(false);
    }
  };

  const fetchTimetables = async () => {
    if (!selectedDosen?.id) return;
    try {
      setIsLoading(true);
      setError(null);
      // Show overlay while fetching timetable data
      setOverlayText("Memuat jadwal dosen...");
      setIsActive(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/dosen/timetable/${selectedDosen.id}?page=1&page_size=10`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!response.ok) {
        throw new Error("Failed to fetch timetable data");
      }
      const data = await response.json();
      if (!data.data || !Array.isArray(data.data)) {
        throw new Error("Invalid timetable data format");
      }
      setTimetableList(data.data);
    } catch (error) {
      console.error("Error fetching timetables:", error);
      setError("Failed to fetch timetable data");
      setTimetableList([]);
    } finally {
      setIsLoading(false);
      setIsActive(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchDosen();
  };

  const handleSelectDosen = (dosen) => {
    setSelectedDosen(dosen);
    setIsModalOpen(false);
    setError(null);
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/timetable/${confirmDelete}`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (!response.ok) throw new Error("Failed to delete timetable");
      // Remove the deleted entry from the timetable list
      setTimetableList((prev) =>
        prev.filter((item) => item.timetable_id !== confirmDelete)
      );
      setConfirmDelete(null);
    } catch (error) {
      console.error("Error deleting timetable:", error);
    }
  };

  const formatTimeRange = (startTime, endTime) => {
    return `${startTime} - ${endTime}`;
  };

  return (
    <div className="space-y-4">
      {/* Dosen Selection */}
      <div>
        <Label>Select Dosen</Label>
        <Input
          value={selectedDosen ? selectedDosen.nama : ""}
          readOnly
          onClick={() => {
            setIsModalOpen(true);
            fetchDosen();
          }}
          placeholder="Click to select dosen..."
          className="cursor-pointer"
        />
      </div>

      {/* Modal for Searching and Selecting Dosen */}
      <Dialog open={isModalOpen} onOpenChange={() => setIsModalOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Select Dosen</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <form onSubmit={handleSearch} className="space-y-2">
              <Label>Search Dosen</Label>
              <div className="flex gap-2">
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Enter name to search..."
                />
                <Button type="submit">Search</Button>
              </div>
            </form>
            {isLoading && <div className="text-center py-4">Loading...</div>}
            {error && <div className="text-red-500 text-sm">{error}</div>}
            {!isLoading && dosenList.length === 0 && !error && (
              <div className="text-center py-4 text-gray-500">
                No dosen found
              </div>
            )}
            {dosenList.length > 0 && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dosenList.map((dosen) => (
                    <TableRow key={dosen.id}>
                      <TableCell>{dosen.id}</TableCell>
                      <TableCell>{dosen.nama}</TableCell>
                      <TableCell>
                        <Button
                          className="border bg-white text-blue-500 border-blue-500"
                          onClick={() => handleSelectDosen(dosen)}
                        >
                          Select
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Timetable Table */}
      <div className="p-4 border rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Timetable:</h3>
        {isLoading && (
          <div className="text-center py-4">Loading timetable...</div>
        )}
        {error && <div className="text-red-500 text-sm">{error}</div>}
        {!isLoading && timetableList.length === 0 && !error && (
          <div className="text-center py-4 text-gray-500">
            No timetable entries found
          </div>
        )}
        {timetableList.length > 0 && (
          <DosenTimetableManagementTable
            timetableList={timetableList}
            onDelete={(id) => setConfirmDelete(id)}
          />
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={confirmDelete !== null}
        onOpenChange={() => setConfirmDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete Timetable</DialogTitle>
          </DialogHeader>
          <p>
            Are you sure you want to delete this timetable entry? This action
            cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDelete(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DosenTimeTableManagement;
