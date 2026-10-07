import type { ReactNode } from 'react';

export interface ToggleProps {
  /** Visible text; also the accessible name. */
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon?: ReactNode;
  disabled?: boolean;
  /** Tooltip, e.g. what the setting does or why it can't be changed. */
  hint?: string;
}
