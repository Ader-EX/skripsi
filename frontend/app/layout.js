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
  icons: {
    icon: [
      {
        media: "(prefers-color-scheme: light)",
        url: "/logo.png",
        href: "/logo.png",
      },
      {
        media: "(prefers-color-scheme: dark)",
        url: "/logo.png",
        href: "/logo.png",
      },
    ],
  },
};

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
      <head>
        <link rel="icon" href="/logo.png" type="image/png" />
      </head>
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}
