import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PreferenceDialog = ({
  isOpen,
  onClose,
  selectedPreference,
  onPreferenceChange,
  onSave,
}) => {
  const reasonOptions = [
    "Jadwal penelitian/riset",
    "Kewajiban keluarga",
    "Jadwal administrasi",
    "Kendala jadwal lainnya",
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className={`${
          selectedPreference?.is_high_priority === 1
            ? "border-t-4 border-t-red-500"
            : "border-t-4 border-t-blue-500"
        }`}
      >
        <DialogHeader>
          <DialogTitle
            className={`${
              selectedPreference?.is_high_priority === 1
                ? "text-red-500"
                : "text-blue-500"
            }`}
          >
            {selectedPreference?.is_high_priority === 1
              ? "Hindari Waktu Ini"
              : "Waktu Yang Diinginkan"}
          </DialogTitle>
          <div className="text-sm text-gray-500">
            {selectedPreference?.is_high_priority === 1
              ? "Sistem akan berusaha untuk TIDAK menjadwalkan kelas Anda di waktu ini"
              : "Sistem akan berusaha untuk menjadwalkan kelas Anda di waktu ini"}
          </div>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex items-center gap-4">
            <Label
              htmlFor="high-priority"
              className={`${
                selectedPreference?.is_high_priority === 1
                  ? "text-red-500"
                  : "text-blue-500"
              }`}
            >
              Hindari Waktu Ini
            </Label>
            <Checkbox
              id="high-priority"
              checked={selectedPreference?.is_high_priority === 1}
              onCheckedChange={(checked) => {
                onPreferenceChange({
                  ...selectedPreference,
                  is_high_priority: checked ? 1 : 0,
                  reason: checked ? selectedPreference?.reason : null,
                });
              }}
            />
          </div>
          <div className="grid gap-2">
            <Label
              className={
                selectedPreference?.is_high_priority === 1
                  ? "text-red-500"
                  : "text-blue-500"
              }
            >
              {selectedPreference?.is_high_priority === 1
                ? "Alasan Tidak Bisa Mengajar"
                : "Catatan (Opsional)"}
            </Label>
            <Select
              value={selectedPreference?.reason || ""}
              onValueChange={(value) => {
                onPreferenceChange({
                  ...selectedPreference,
                  reason: value,
                });
              }}
              disabled={selectedPreference?.is_high_priority !== 1}
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={
                    selectedPreference?.is_high_priority === 1
                      ? "Pilih alasan"
                      : "Tambahkan catatan"
                  }
                />
              </SelectTrigger>
              <SelectContent className="bg-white">
                {reasonOptions.map((reason) => (
                  <SelectItem key={reason} value={reason}>
                    {reason}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Batal
          </Button>
          <Button
            onClick={onSave}
            variant={
              selectedPreference?.is_high_priority === 1
                ? "destructive"
                : "default"
            }
          >
            Simpan
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PreferenceDialog;
