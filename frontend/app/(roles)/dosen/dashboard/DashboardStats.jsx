"use client";

import React, { useEffect, useState } from "react";
import Cookies from "js-cookie"; // Import CookiesJS

import { Book, Users, School } from "lucide-react";
import { decodeToken } from "@/utils/decoder";
import { DashboardStatsCard } from "@/components/global/DashboardStatsCard";

const DashboardStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Get token from cookies
        const token = Cookies.get("access_token");

        const payload = decodeToken(token);

        // Fetch dashboard stats
        const statsResponse = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/dosen/dashboard-stats/${payload.role_id}`,
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
      <DashboardStatsCard
        value={stats.mata_kuliah.count}
        label={stats.mata_kuliah.label}
        icon={<Book className="w-6 h-6 text-blue-600" />}
      />
      <DashboardStatsCard
        value={stats.ruangan.count}
        label={stats.ruangan.label}
        icon={<School className="w-6 h-6 text-green-600" />}
      />
      <DashboardStatsCard
        value={stats.classes_taught.count}
        label={stats.classes_taught.label}
        icon={<Users className="w-6 h-6 text-purple-600" />}
      />
    </div>
  );
};

export default DashboardStats;
