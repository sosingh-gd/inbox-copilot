import type { ReactNode } from 'react';

export interface AppShellTemplateProps {
  header: ReactNode;
  /** Leave out for a page without a sidebar; the sidebar props below are then unused. */
  sidebar?: ReactNode;
  /** Shown above the sidebar when it opens as a drawer on small screens. */
  sidebarTitle?: string;
  isSidebarOpen?: boolean;
  onSidebarClose?: () => void;
  children: ReactNode;
}
