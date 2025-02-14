import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const MataKuliahForm = ({
  isOpen,
  onClose,
  isEdit,
  matakuliah,
  fetchMataKuliah,
  programStudi,
}) => {
  // Form submit logic here...

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Edit Mata Kuliah" : "Tambah Mata Kuliah Baru"}
          </DialogTitle>
        </DialogHeader>
        {/* Form fields go here */}
        <Button onClick={onClose}>Tutup</Button>
      </DialogContent>
    </Dialog>
  );
};

export default MataKuliahForm;
