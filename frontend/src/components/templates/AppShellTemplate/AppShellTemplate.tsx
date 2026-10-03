import { X } from 'lucide-react';
import { cn } from '@/utils/cn';
import { IconButton } from '../../atoms/IconButton';
import type { AppShellTemplateProps } from './AppShellTemplate.types';

/** Full-height layout: header on top, sidebar (a drawer below `lg`) and main content. */
export function AppShellTemplate({
  header,
  sidebar,
  sidebarTitle,
  isSidebarOpen,
  onSidebarClose,
  children,
}: AppShellTemplateProps) {
  const closeLabel = `Close ${sidebarTitle.toLowerCase()}`;
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-50 text-ink">
      {header}
      <div className="relative flex min-h-0 flex-1">
        {isSidebarOpen && (
          <button
            aria-label={closeLabel}
            className="fixed inset-0 z-20 bg-slate-950/25 lg:hidden"
            onClick={onSidebarClose}
            type="button"
          />
        )}
        <aside
          className={cn(
            'fixed inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-slate-200 bg-white transition-transform',
            'lg:static lg:z-auto lg:translate-x-0',
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4 lg:hidden">
            <span className="font-semibold">{sidebarTitle}</span>
            <IconButton
              icon={<X className="h-5 w-5" />}
              label={closeLabel}
              onClick={onSidebarClose}
              size="sm"
            />
          </div>
          {sidebar}
        </aside>
        <main className="flex min-w-0 flex-1 flex-col bg-white">{children}</main>
      </div>
    </div>
  );
}
