import { Menu } from 'lucide-react';
import { BrandMark } from '../../atoms/BrandMark';
import { IconButton } from '../../atoms/IconButton';
import type { AppHeaderProps } from './AppHeader.types';

export function AppHeader({ onMenuClick, menuLabel = 'Open menu', actions }: AppHeaderProps) {
  return (
    <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-4 sm:px-6">
      <IconButton
        className="mr-3 lg:hidden"
        icon={<Menu className="h-5 w-5" />}
        label={menuLabel}
        onClick={onMenuClick}
      />
      <div className="flex items-center gap-3">
        <BrandMark />
        <span className="text-lg font-semibold text-ink">Inbox Copilot</span>
      </div>
      <div className="ml-auto flex items-center gap-3">{actions}</div>
    </header>
  );
}
