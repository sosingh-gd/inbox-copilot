import type { ReactNode } from 'react';

export interface AppHeaderProps {
  /** Opens the sidebar on small screens. */
  onMenuClick: () => void;
  menuLabel?: string;
  /** Right-aligned slot, e.g. the user menu. */
  actions?: ReactNode;
}
