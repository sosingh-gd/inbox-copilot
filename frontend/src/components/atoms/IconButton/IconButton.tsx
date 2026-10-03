import { cn } from '@/utils/cn';
import type { IconButtonProps } from './IconButton.types';

const variantClasses = {
  primary: 'bg-brand text-white hover:bg-brand-deep disabled:bg-slate-300',
  ghost: 'text-ink-soft hover:bg-slate-100',
} as const;

const sizeClasses = { sm: 'h-9 w-9', md: 'h-10 w-10' } as const;

export function IconButton({
  icon,
  label,
  variant = 'ghost',
  size = 'md',
  type = 'button',
  disabled = false,
  onClick,
  className,
}: IconButtonProps) {
  return (
    <button
      aria-label={label}
      className={cn(
        'grid shrink-0 place-items-center rounded-md transition',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/20',
        'disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      disabled={disabled}
      onClick={onClick}
      title={label}
      type={type}
    >
      {icon}
    </button>
  );
}
