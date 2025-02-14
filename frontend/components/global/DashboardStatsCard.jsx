import { Card } from "../ui/card";

export const DashboardStatsCard = ({ value, label, icon }) => (
  <Card className="flex items-center justify-between p-6 space-x-4 shadow-md border rounded-lg">
    <div className="flex items-center justify-center w-12 h-12 rounded-full bg-gray-100">
      {icon}
    </div>
    <div className="flex-1 text-right">
      <div className="text-3xl font-bold">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  </Card>
);
