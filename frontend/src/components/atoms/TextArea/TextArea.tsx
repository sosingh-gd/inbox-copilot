import type { TextAreaProps } from './TextArea.types';

/** Borderless, auto-growing (up to a limit) text area meant to sit inside a framed container. */
export function TextArea({
  value,
  onChange,
  onKeyDown,
  'aria-label': ariaLabel,
  placeholder,
  rows = 1,
  disabled = false,
}: TextAreaProps) {
  return (
    <textarea
      aria-label={ariaLabel}
      className="field-sizing-content max-h-32 min-h-11 flex-1 resize-none bg-transparent px-2 py-2.5 text-sm leading-5 text-ink outline-none placeholder:text-ink-muted"
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      rows={rows}
      value={value}
    />
  );
}
