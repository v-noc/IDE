import { create } from 'zustand';
import type { ThemeConfig } from '@/types/project';




interface ThemeState {
    theme: ThemeConfig | undefined;
    setTheme: (theme: ThemeConfig | undefined) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
    theme: {
        leftSidebarColor: "#f9f9f9",
        rightSidebarColor: "#f9f9f9",
    },
    setTheme: (theme) => set({ theme }),
}));
