import { cn } from '@/utils/cn';
import type { StatusTextProps } from './StatusText.types';

const toneClasses = {
  error: 'text-danger',
  success: 'text-success',
  muted: 'text-ink-muted',
} as const;

/** A short status or error line that screen readers announce when it changes. */
export function StatusText({ children, tone = 'muted', align = 'left' }: StatusTextProps) {
  return (
    <p
      aria-live="polite"
      className={cn('text-sm', toneClasses[tone], align === 'center' && 'text-center')}
      role={tone === 'error' ? 'alert' : undefined}
    >
      {children}
    </p>
  );
}
