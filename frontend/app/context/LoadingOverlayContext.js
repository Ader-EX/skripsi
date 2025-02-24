"use client";
import React, { createContext, useState, useContext } from "react";

const LoadingOverlayContext = createContext();

export const LoadingOverlayProvider = ({ children }) => {
  const [isActive, setIsActive] = useState(false);
  const [overlayText, setOverlayText] = useState("Loading...");

  return (
    <LoadingOverlayContext.Provider
      value={{ isActive, setIsActive, overlayText, setOverlayText }}
    >
      {children}
    </LoadingOverlayContext.Provider>
  );
};

export const useLoadingOverlay = () => useContext(LoadingOverlayContext);
