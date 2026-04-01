import { QueryClient } from '@tanstack/react-query';

/** Shared client for stores and hooks outside React tree boundaries. */
export const queryClient = new QueryClient();
