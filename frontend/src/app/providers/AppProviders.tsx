import { GoogleOAuthProvider } from '@react-oauth/google';
import { QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { env } from '@/config/env';
import { queryClient } from '@/lib/queryClient';

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <GoogleOAuthProvider clientId={env.googleClientId}>{children}</GoogleOAuthProvider>
    </QueryClientProvider>
  );
}
