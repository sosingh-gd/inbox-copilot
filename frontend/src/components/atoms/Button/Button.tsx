import { cn } from '@/utils/cn';
import { Spinner } from '../Spinner';
import type { ButtonProps, ButtonSize, ButtonVariant } from './Button.types';

const variantClasses: Record<ButtonVariant, string> = {
  primary: 'bg-brand text-white hover:bg-brand-deep shadow-sm',
  secondary:
    'border border-slate-200 bg-white text-ink shadow-sm hover:border-brand/40 hover:shadow-md',
  ghost: 'text-ink-soft hover:bg-slate-100',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-14 px-5 text-base',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  disabled = false,
  loading = false,
  startIcon,
  fullWidth = false,
  onClick,
  'aria-label': ariaLabel,
}: ButtonProps) {
  return (
    <button
      aria-busy={loading || undefined}
      aria-label={ariaLabel}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition',
        'focus:outline-none focus-visible:ring-4 focus-visible:ring-brand/20',
        'disabled:cursor-not-allowed disabled:opacity-60',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
      )}
      disabled={disabled || loading}
      onClick={onClick}
      type={type}
    >
      {loading ? <Spinner size="sm" /> : startIcon}
      {children}
    </button>
  );
}
