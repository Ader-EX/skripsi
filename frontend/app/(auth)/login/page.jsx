"use client";
import React from "react";
import Image from "next/image";
import { useForm } from "react-hook-form";
import newImage from "@/public/login.jpg";
import toast from "react-hot-toast";
import useAuthStore from "@/hooks/useAuthStore";
import Link from "next/link";
import { Timer } from "lucide-react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";

const Login = () => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();
  const { setAuth } = useAuthStore();
  const router = useRouter();
  const onSubmit = async (data) => {
    toast.loading("Logging in...");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/user/token`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            nim_nip: data.username,
            password: data.password,
            role: "mahasiswa",
          }),
        }
      );
      const result = await response.json();
      if (response.ok) {
        toast.dismiss();
        toast.success("Login successful!");

        Cookies.set("access_token", result.access_token);
        Cookies.set("token_type", result.token_type);
        Cookies.set("role", result.role);
        router.push(`/${result.role}/dashboard`);
      } else {
        toast.dismiss();
        toast.error(result.detail || "Invalid credentials");
      }
    } catch (error) {
      toast.dismiss();
      console.log(error.detail || "Invalid credentials");
      toast.error("Something went wrong. Please try again.");
    }
  };
  return (
    <div className="bg-gray-100 flex justify-center items-center h-screen">
      {/* Left: Image */}
      <div className="w-1/2 h-screen hidden lg:block relative">
        <div className=" h-full absolute bg-primary w-full opacity-40"></div>
        <Image
          src={newImage}
          alt="Placeholder Image"
          width={800}
          height={600}
          className="object-cover w-full h-full"
        />
      </div>

      {/* Right: Login Form */}
      <div className="lg:p-36 md:p-52 sm:20 p-8 w-full lg:w-1/2">
        <Link href="/">
          <h1 className="text-2xl font-bold text-primary flex gap-x-2 mb-4">
            <Timer className="self-center" />
            <span>GenPlan</span>
          </h1>
        </Link>

        <h1 className="text-2xl font-semibold mb-4">Login</h1>
        <form action="#" method="POST" onSubmit={handleSubmit(onSubmit)}>
          {/* Username Input */}
          <div className="mb-4">
            <label htmlFor="username" className="block text-gray-600">
              NIM / NIP
            </label>
            <input
              type="text"
              id="username"
              name="username"
              {...register("username", { required: true })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
              autoComplete="off"
            />
          </div>

          {/* Password Input */}
          <div className="mb-4">
            <label htmlFor="password" className="block text-gray-600">
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              {...register("password", { required: true })}
              className="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
              autoComplete="off"
            />
          </div>
          {/* 
          <div className="mb-4 flex items-center">
            <input
              type="checkbox"
              id="remember"
              name="remember"
              {...register("remember")}
              className="text-blue-500"
            />
            <label htmlFor="remember" className="text-gray-600 ml-2">
              Remember Me
            </label>
          </div>  */}

          {/* Forgot Password Link */}
          <div className="mb-6 text-blue-500">
            <a href="#" className="hover:underline">
              Forgot Password
            </a>
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={watch("remember") && !errors.username && !errors.password}
            className="bg-blue-500 hover:bg-blue-600 text-white font-semibold rounded-md py-2 px-4 w-full"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
