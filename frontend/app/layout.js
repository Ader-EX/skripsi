import localFont from "next/font/local";
import "./globals.css";

import { LoadingOverlay } from "@/components/global/CustomLoadingOverlay";
import {
  LoadingOverlayProvider,
  useLoadingOverlay,
} from "./context/LoadingOverlayContext";
import ClientProviders from "./context/ClientProvider";

export const metadata = {
  title: "GenPlan Scheduler",
  description: "Next Generation Scheduler",
};

// Create a wrapper component to use the global overlay state
const LayoutWithOverlay = ({ children }) => {
  const { isActive, overlayText } = useLoadingOverlay();
  return (
    <LoadingOverlay active={isActive} text={overlayText}>
      {children}
    </LoadingOverlay>
  );
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
