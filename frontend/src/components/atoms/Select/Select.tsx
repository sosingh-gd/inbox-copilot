import type { SelectProps } from './Select.types';

export function Select<T extends string>({
  options,
  value,
  onChange,
  'aria-label': ariaLabel,
  icon,
}: SelectProps<T>) {
  return (
    <label className="flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-sm focus-within:border-brand">
      {icon}
      <select
        aria-label={ariaLabel}
        className="bg-transparent font-medium text-ink outline-none"
        onChange={(event) => {
          const selected = options.find((option) => option.value === event.target.value);
          if (selected) onChange(selected.value);
        }}
        value={value}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
