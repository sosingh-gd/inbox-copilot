import { cn } from '@/utils/cn';
import type { AvatarProps } from './Avatar.types';

const toneClasses = {
  brand: 'bg-brand text-white',
  warm: 'bg-amber-100 text-amber-800',
} as const;

export function Avatar({ children, tone = 'brand' }: AvatarProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'grid h-8 w-8 shrink-0 place-items-center rounded-md text-xs font-semibold',
        toneClasses[tone],
      )}
    >
      {children}
    </span>
  );
}
