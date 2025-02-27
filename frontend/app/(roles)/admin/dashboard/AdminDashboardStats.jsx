"use client";

import React, { useEffect, useState } from "react";
import Cookies from "js-cookie"; // Import CookiesJS

import { Book, Users, School, BookCheck } from "lucide-react";
import { decodeToken } from "@/utils/decoder";
import { DashboardStatsCard } from "@/components/global/DashboardStatsCard";

const AdminDashboardStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Get token from cookies
        const token = Cookies.get("access_token");

        const payload = decodeToken(token);

        const API_URL = process.env.NEXT_PUBLIC_API_URL;

        // Fetch dashboard stats
        const statsResponse = await fetch(`${API_URL}/admin/dashboard-stats`, {
          headers: { Authorization: `Bearer ${token}` },
        });
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
        value={stats.mata_kuliah_dibuka.count}
        label={stats.mata_kuliah_dibuka.label}
        icon={<BookCheck className="w-6 h-6 text-orange-600" />}
      />
      <DashboardStatsCard
        value={stats.ruangan.count}
        label={stats.ruangan.label}
        icon={<School className="w-6 h-6 text-green-600" />}
      />
      <DashboardStatsCard
        value={stats.dosen.count}
        label={stats.dosen.label}
        icon={<Users className="w-6 h-6 text-purple-600" />}
      />
    </div>
  );
};

export default AdminDashboardStats;
