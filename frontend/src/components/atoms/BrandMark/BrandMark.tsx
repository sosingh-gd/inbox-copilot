import { Sparkles } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { BrandMarkProps } from './BrandMark.types';

export function BrandMark({ pulse = false }: BrandMarkProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        'grid h-9 w-9 shrink-0 place-items-center rounded-md bg-brand text-white',
        pulse && 'animate-pulse',
      )}
    >
      <Sparkles className="h-5 w-5" />
    </span>
  );
}
