import type { ReactNode } from 'react';

export interface AppShellTemplateProps {
  header: ReactNode;
  sidebar: ReactNode;
  /** Shown above the sidebar when it opens as a drawer on small screens. */
  sidebarTitle: string;
  isSidebarOpen: boolean;
  onSidebarClose: () => void;
  children: ReactNode;
}
