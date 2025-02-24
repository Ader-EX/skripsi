"use client";
import React from "react";

import Navbar from "@/components/global/Navbar";
import { Toaster } from "react-hot-toast";
import { usePathname } from "next/navigation";
import { LoadingOverlayProvider } from "./LoadingOverlayContext";
import OverlayWrapper from "@/components/global/OverlayWrapper";

export default function ClientProviders({ children }) {
  const pathname = usePathname();

  return (
    <LoadingOverlayProvider>
      <Toaster position="bottom-right" reverseOrder={false} />
      {/* <Navbar /> */}
      {pathname.startsWith("/admin") ? (
        <OverlayWrapper>{children}</OverlayWrapper>
      ) : (
        children
      )}
    </LoadingOverlayProvider>
  );
}
