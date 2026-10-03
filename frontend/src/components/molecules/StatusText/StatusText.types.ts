import type { ReactNode } from 'react';

export interface StatusTextProps {
  children: ReactNode;
  tone?: 'error' | 'success' | 'muted';
  align?: 'left' | 'center';
}
