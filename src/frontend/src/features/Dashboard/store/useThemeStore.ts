import { create } from 'zustand';

export interface ThemeConfig {
    navbarColor: string;
    leftSidebarColor: string;
    rightSidebarColor: string;
    backgroundColor: string;
    textColor: string;
    iconColor: string;
    cardColor: string;
    nameColor: string;
}

interface ThemeState {
    theme: ThemeConfig | undefined;
    setTheme: (theme: ThemeConfig | undefined) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
    theme: undefined,
    setTheme: (theme) => set({ theme }),
}));
