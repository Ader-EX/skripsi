import { create } from "zustand";

const useAuthStore = create((set) => ({
  token: null,
  tokenType: null,
  role: null,
  setAuth: (token, tokenType, role) => {
    set({ token, tokenType, role });
  },
  logout: () => set({ token: null, tokenType: null }),
}));

export default useAuthStore;
