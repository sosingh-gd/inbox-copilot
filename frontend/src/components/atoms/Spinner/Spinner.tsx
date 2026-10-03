import { cn } from '@/utils/cn';
import type { SpinnerProps } from './Spinner.types';

const sizeClasses = { sm: 'h-4 w-4 border-2', md: 'h-6 w-6 border-2' } as const;

export function Spinner({ size = 'md', label }: SpinnerProps) {
  return (
    <span
      aria-hidden={label ? undefined : true}
      aria-label={label}
      className={cn(
        'inline-block animate-spin rounded-full border-current border-r-transparent',
        sizeClasses[size],
      )}
      role={label ? 'status' : undefined}
    />
  );
}
