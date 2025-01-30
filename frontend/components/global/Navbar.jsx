"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, Search, Timer } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import useAuthStore from "@/hooks/useAuthStore";
import { useRouter } from "next/navigation";

export default function Navbar() {
  const [state, setState] = React.useState(false);
  const { token, logout } = useAuthStore();
  console.log("Navbar token:", token);
  const router = useRouter();

  React.useEffect(() => {
    console.log("Token updated:", token);
  }, [token]);

  const handleLogout = () => {
    logout();
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
        <div
          className={`flex-1 justify-self-center pb-3 mt-8 md:block md:pb-0 md:mt-0 ${
            state ? "block" : "hidden"
          }`}
        >
          <ul className="justify-end items-center space-y-8 md:flex md:space-x-6 md:space-y-0">
            {token ? (
              <>
                <p className="text-primary font-bold">Admin</p>
                <Avatar>
                  <AvatarImage src="https://github.com/shadcn.png" />
                  <AvatarFallback>CN</AvatarFallback>
                </Avatar>
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
