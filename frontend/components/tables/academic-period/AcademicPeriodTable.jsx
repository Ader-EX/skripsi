import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, CheckCircle } from "lucide-react";

const AcademicPeriodTable = ({
  academicPeriods,
  onEdit,
  onDelete,
  onActivate,
}) => {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="bg-primary/5">
            <TableHead>Tahun Ajaran</TableHead>
            <TableHead>Semester</TableHead>
            <TableHead>Start Date</TableHead>
            <TableHead>End Date</TableHead>
            <TableHead>Active</TableHead>
            <TableHead className="text-right">Aksi</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {academicPeriods.length > 0 ? (
            academicPeriods.map((period) => (
              <TableRow key={period.id}>
                <TableCell>{period.tahun_ajaran}</TableCell>
                <TableCell>{period.semester}</TableCell>
                <TableCell>{period.start_date}</TableCell>
                <TableCell>{period.end_date}</TableCell>
                <TableCell>
                  {period.is_active ? (
                    <span className="text-green-500 font-semibold">Active</span>
                  ) : (
                    <span className="text-gray-400">Inactive</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8 text-blue-500 hover:text-blue-600"
                      onClick={() => onEdit(period)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="icon"
                      className="h-8 w-8 text-red-500 hover:text-red-600"
                      onClick={() => onDelete(period.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    {!period.is_active && (
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 text-green-500 hover:text-green-600"
                        onClick={() => onActivate(period.id)}
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="text-center h-32">
                <div className="flex items-center justify-center">
                  Tidak ada data akademik.
                </div>
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default AcademicPeriodTable;
