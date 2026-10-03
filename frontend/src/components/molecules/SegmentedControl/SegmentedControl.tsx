import { cn } from '@/utils/cn';
import type { SegmentedControlProps } from './SegmentedControl.types';

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  'aria-label': ariaLabel,
  icon,
}: SegmentedControlProps<T>) {
  return (
    <div
      aria-label={ariaLabel}
      className="flex h-10 items-center gap-1 rounded-md border border-slate-200 bg-slate-50 p-1 pl-2"
      role="radiogroup"
    >
      {icon}
      {options.map((option) => {
        const isSelected = option.value === value;
        return (
          <button
            aria-checked={isSelected}
            className={cn(
              'h-8 rounded px-2.5 text-xs font-medium',
              isSelected ? 'bg-white text-ink shadow-sm' : 'text-ink-muted hover:text-ink',
            )}
            key={option.value}
            onClick={() => onChange(option.value)}
            role="radio"
            type="button"
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
