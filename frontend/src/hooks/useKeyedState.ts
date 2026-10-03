import { useCallback, useState } from 'react';

/**
 * Local state that falls back to `initial` whenever `key` changes, e.g. a draft per
 * conversation. Derived during render, so there's no effect and no stale flash.
 */
export function useKeyedState<T>(key: string, initial: T): [T, (value: T) => void] {
  const [state, setState] = useState<{ key: string; value: T } | null>(null);
  const value = state !== null && state.key === key ? state.value : initial;
  const setValue = useCallback((next: T) => setState({ key, value: next }), [key]);
  return [value, setValue];
}
