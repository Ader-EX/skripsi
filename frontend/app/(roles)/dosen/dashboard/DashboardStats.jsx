"use client";

import React, { useEffect, useState } from "react";
import Cookies from "js-cookie"; // Import CookiesJS

import { Card } from "@/components/ui/card";
import { Book, Users, School } from "lucide-react";
import { decodeToken } from "@/utils/decoder";

const StatsCard = ({ value, label, icon }) => (
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

const DashboardStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Get token from cookies
        const token = Cookies.get("access_token");
        if (!token) {
          throw new Error("No authentication token found.");
        }

        // Decode JWT token
        const payload = decodeToken(token);
        if (!payload || !payload.sub) {
          throw new Error("Invalid token format.");
        }

        // Encode email and fetch user details
        const encodedEmail = encodeURIComponent(payload.sub);
        const API_URL = process.env.NEXT_PUBLIC_API_URL;

        const userResponse = await fetch(
          `${API_URL}/user/details?email=${encodedEmail}`
        );
        if (!userResponse.ok) throw new Error("Failed to fetch user details.");

        const userData = await userResponse.json();
        const userId = userData.id;

        // Fetch dashboard stats
        const statsResponse = await fetch(
          `${API_URL}/dosen/dashboard-stats/${userId}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        if (!statsResponse.ok)
          throw new Error("Failed to fetch dashboard stats.");

        const statsData = await statsResponse.json();
        setStats(statsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading)
    return <p className="text-center text-gray-500">Loading stats...</p>;
  if (error) return <p className="text-center text-red-500">Error: {error}</p>;

  return (
    <div className="flex w-full sm:flex-row flex-col space-y-4 sm:space-y-0 sm:space-x-4">
      <StatsCard
        value={stats.mata_kuliah.count}
        label={stats.mata_kuliah.label}
        icon={<Book className="w-6 h-6 text-blue-600" />}
      />
      <StatsCard
        value={stats.ruangan.count}
        label={stats.ruangan.label}
        icon={<School className="w-6 h-6 text-green-600" />}
      />
      <StatsCard
        value={stats.classes_taught.count}
        label={stats.classes_taught.label}
        icon={<Users className="w-6 h-6 text-purple-600" />}
      />
    </div>
  );
};

export default DashboardStats;
