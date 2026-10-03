import type { KeyboardEventHandler } from 'react';

export interface TextAreaProps {
  value: string;
  onChange: (value: string) => void;
  onKeyDown?: KeyboardEventHandler<HTMLTextAreaElement>;
  'aria-label': string;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
}
