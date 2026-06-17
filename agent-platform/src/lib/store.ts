"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  favorites: string[];
  toggleFavorite: (id: string) => void;
  cmdkOpen: boolean;
  setCmdk: (v: boolean) => void;
}

export const useUI = create<UIState>()(
  persist(
    (set) => ({
      favorites: [],
      toggleFavorite: (id) =>
        set((s) => ({
          favorites: s.favorites.includes(id)
            ? s.favorites.filter((f) => f !== id)
            : [...s.favorites, id],
        })),
      cmdkOpen: false,
      setCmdk: (v) => set({ cmdkOpen: v }),
    }),
    { name: "agent-platform-ui" }
  )
);
