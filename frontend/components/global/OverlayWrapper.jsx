"use client";
import React from "react";

import { LoadingOverlay } from "./CustomLoadingOverlay";
import { useLoadingOverlay } from "@/app/context/LoadingOverlayContext";

const OverlayWrapper = ({ children }) => {
  const { isActive, overlayText } = useLoadingOverlay();

  return (
    <LoadingOverlay active={isActive} text={overlayText}>
      {children}
    </LoadingOverlay>
  );
};

export default OverlayWrapper;
