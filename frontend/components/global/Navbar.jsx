"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, Search, Timer } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import useAuthStore from "@/hooks/useAuthStore";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { jwtDecode } from "jwt-decode";

export default function Navbar() {
  const [state, setState] = React.useState(false);
  const { token, logout } = useAuthStore();
  const router = useRouter();

  const hasil = Cookies.get("access_token");

  let role = "";
  if (hasil) {
    try {
      const decoded = jwtDecode(hasil);
      role = decoded.role || "guest";
    } catch (error) {
      console.error("JWT Decode Error:", error);
    }
  }

  // Define role-based dashboard URL
  const dashboardUrl =
    role === "mahasiswa"
      ? "/mahasiswa/dashboard"
      : role === "dosen"
      ? "/dosen/dashboard"
      : role === "admin"
      ? "/admin/dashboard"
      : "/";

  const handleLogout = () => {
    logout();
    Cookies.remove("access_token");
    router.push("/");
  };

  return (
    <nav className="bg-white w-full border-b md:border-1">
      <div className="items-center px-4 max-w-screen-xl mx-auto md:flex md:px-8">
        <div className="flex items-center justify-between py-3 md:py-5 md:block">
          <Link href="/">
            <h1 className="text-2xl font-bold text-primary flex gap-x-2">
              <Timer className="self-center" />
              <span>GenPlan</span>
            </h1>
          </Link>
          <div className="md:hidden">
            <button
              className="text-gray-700 outline-none p-2 rounded-md focus:border-gray-400 focus:border"
              onClick={() => setState(!state)}
            >
              <Menu />
            </button>
          </div>
        </div>

        {/* Navbar Menu */}
        <div
          className={`flex-1 justify-self-center pb-3 mt-8 md:block md:pb-0 md:mt-0 ${
            state ? "block" : "hidden"
          }`}
        >
          <ul className="justify-end items-center space-y-8 md:flex md:space-x-6 md:space-y-0">
            {hasil ? (
              <>
                {/* Dashboard Button */}
                <Link href={dashboardUrl}>
                  <button className="bg-primary text-white py-2 px-4 rounded-md hover:bg-primary/80 transition">
                    Go to Dashboard
                  </button>
                </Link>

                {/* User Avatar */}

                {/* Logout Button */}
                <button
                  onClick={handleLogout}
                  className="text-red-500 hover:underline"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link href="/login">
                <button className="bg-blue-500 text-white py-2 px-4 rounded-md">
                  Login
                </button>
              </Link>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}
