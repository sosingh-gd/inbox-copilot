import type { MouseEventHandler, ReactNode } from 'react';

export interface IconButtonProps {
  icon: ReactNode;
  /** Accessible name; also shown as a tooltip. Required because there is no visible text. */
  label: string;
  variant?: 'primary' | 'ghost';
  size?: 'sm' | 'md';
  type?: 'button' | 'submit';
  disabled?: boolean;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  className?: string;
}
