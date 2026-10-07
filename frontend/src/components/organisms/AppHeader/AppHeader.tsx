import { Menu } from 'lucide-react';
import { NavLink } from 'react-router';
import { navItems } from '@/config/routes';
import { cn } from '@/utils/cn';
import { BrandMark } from '../../atoms/BrandMark';
import { IconButton } from '../../atoms/IconButton';
import type { AppHeaderProps } from './AppHeader.types';

export function AppHeader({ onMenuClick, menuLabel = 'Open menu', actions }: AppHeaderProps) {
  return (
    <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-4 sm:px-6">
      {onMenuClick && (
        <IconButton
          className="mr-3 lg:hidden"
          icon={<Menu className="h-5 w-5" />}
          label={menuLabel}
          onClick={onMenuClick}
        />
      )}
      <div className="flex items-center gap-3">
        <BrandMark />
        <span className="hidden text-lg font-semibold text-ink sm:inline">Inbox Copilot</span>
      </div>
      <nav aria-label="Main" className="ml-4 flex items-center gap-1 sm:ml-8">
        {navItems.map((item) => (
          <NavLink
            className={({ isActive }) =>
              cn(
                'rounded-md px-3 py-2 text-sm font-medium transition',
                isActive ? 'bg-blue-50 text-brand-deep' : 'text-ink-soft hover:bg-slate-100',
              )
            }
            key={item.to}
            to={item.to}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3">{actions}</div>
    </header>
  );
}
