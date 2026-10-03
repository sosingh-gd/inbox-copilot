import type { MouseEventHandler, ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  type?: 'button' | 'submit';
  disabled?: boolean;
  /** Shows a spinner and disables the button. */
  loading?: boolean;
  startIcon?: ReactNode;
  fullWidth?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  'aria-label'?: string;
}
