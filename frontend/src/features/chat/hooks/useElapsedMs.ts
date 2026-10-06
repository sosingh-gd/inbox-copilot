import { useEffect, useState } from 'react';

const TICK_MS = 100;

/** Milliseconds since `startedAt`, updated every tick while the calling component is mounted. */
export function useElapsedMs(startedAt: number): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(timer);
  }, []);

  return Math.max(0, now - startedAt);
}
