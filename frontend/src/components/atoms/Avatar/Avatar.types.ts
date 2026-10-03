import type { ReactNode } from 'react';

export interface AvatarProps {
  /** An initial or an icon. */
  children: ReactNode;
  tone?: 'brand' | 'warm';
}
