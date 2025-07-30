import { create } from 'zustand';

type ViewFormat = 'grid' | 'list';

interface AppState {
  viewFormat: ViewFormat;
  setViewFormat: (format: ViewFormat) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  viewFormat: 'grid',
  setViewFormat: (format) => set({ viewFormat: format }),
  searchTerm: '',
  setSearchTerm: (term) => set({ searchTerm: term }),
}));
