import { create } from 'zustand';
import type { ThemeConfig } from '@/types/project';




interface ThemeState {
    theme: ThemeConfig | undefined;
    setTheme: (theme: ThemeConfig | undefined) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
    theme: undefined,
    setTheme: (theme) => set({ theme }),
}));
