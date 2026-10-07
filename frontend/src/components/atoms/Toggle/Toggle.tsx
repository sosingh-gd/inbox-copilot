import { cn } from '@/utils/cn';
import type { ToggleProps } from './Toggle.types';

/** An on/off switch with a label, sized to sit next to Select and SegmentedControl. */
export function Toggle({ label, checked, onChange, icon, disabled = false, hint }: ToggleProps) {
  return (
    <button
      aria-checked={checked}
      className={cn(
        'flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm font-medium text-ink transition',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/20',
        'disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-ink-muted',
      )}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      role="switch"
      title={hint}
      type="button"
    >
      {icon}
      {label}
      <span
        className={cn(
          'relative h-5 w-9 shrink-0 rounded-full transition-colors',
          checked ? 'bg-brand' : 'bg-slate-300',
          disabled && 'opacity-60',
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform',
            checked && 'translate-x-4',
          )}
        />
      </span>
    </button>
  );
}
