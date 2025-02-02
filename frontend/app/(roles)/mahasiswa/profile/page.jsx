import React from "react";
import { Card } from "@/components/ui/card";

const MahasiswaProfile = () => {
  return (
    <div className="flex p-4 w-full">
      <Card className="bg-surface border-border p-6 space-y-6">
        {/* Basic Information */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Basic Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="nama"
              >
                Nama Lengkap
              </label>
              <input
                type="text"
                id="nama"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter full name"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="tglLahir"
              >
                Tanggal Lahir
              </label>
              <input
                type="date"
                id="tglLahir"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary focus:border-primary focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="kotaLahir"
              >
                Kota Lahir
              </label>
              <input
                type="text"
                id="kotaLahir"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter birthplace"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="jenisKelamin"
              >
                Jenis Kelamin
              </label>
              <select
                id="jenisKelamin"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary focus:border-primary focus:ring-1 focus:ring-primary"
              >
                <option value="Laki-laki">Laki-laki</option>
                <option value="Perempuan">Perempuan</option>
              </select>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Contact Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="alamat"
              >
                Alamat
              </label>
              <input
                type="text"
                id="alamat"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter address"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="kodePos"
              >
                Kode Pos
              </label>
              <input
                type="number"
                id="kodePos"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter postal code"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="hp"
              >
                No HP
              </label>
              <input
                type="text"
                id="hp"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter phone number"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="email"
              >
                Email
              </label>
              <input
                type="email"
                id="email"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter email"
              />
            </div>
          </div>
        </div>

        {/* Family Information */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Family Information
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="namaAyah"
              >
                Nama Ayah
              </label>
              <input
                type="text"
                id="namaAyah"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter father's name"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="pekerjaanAyah"
              >
                Pekerjaan Ayah
              </label>
              <input
                type="text"
                id="pekerjaanAyah"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter father's occupation"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="namaIbu"
              >
                Nama Ibu
              </label>
              <input
                type="text"
                id="namaIbu"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter mother's name"
              />
            </div>

            <div>
              <label
                className="block text-sm font-medium text-text-primary mb-1"
                htmlFor="pekerjaanIbu"
              >
                Pekerjaan Ibu
              </label>
              <input
                type="text"
                id="pekerjaanIbu"
                className="w-full p-2 border-border border rounded-md bg-background text-text-primary placeholder:text-text-disabled focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="Enter mother's occupation"
              />
            </div>
          </div>
        </div>

        {/* Marital Status */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Marital Status
          </h2>
          <div>
            <label
              className="block text-sm font-medium text-text-primary mb-1"
              htmlFor="statusKawin"
            >
              Status Kawin
            </label>
            <select
              id="statusKawin"
              className="w-full p-2 border-border border rounded-md bg-background text-text-primary focus:border-primary focus:ring-1 focus:ring-primary"
            >
              <option value="false">Belum Menikah</option>
              <option value="true">Sudah Menikah</option>
            </select>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button className="px-4 py-2 border border-border rounded-md hover:bg-surface text-text-primary transition-colors">
            Cancel
          </button>
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
            Save Changes
          </button>
        </div>
      </Card>
    </div>
  );
};

export default MahasiswaProfile;
