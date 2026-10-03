import { QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import type { ReactElement, ReactNode } from 'react';
import { createQueryClient } from '@/lib/queryClient';

/** Render with a fresh query client per test, so cached data never leaks between tests. */
export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  const queryClient = createQueryClient();
  queryClient.setDefaultOptions({ queries: { retry: false } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  return { queryClient, ...render(ui, { wrapper, ...options }) };
}
