const DOTS = ['first', 'second', 'third'] as const;

/** Shown in place of a reply that has no thinking or text yet. */
export function TypingIndicator() {
  return (
    <div
      aria-label="Inbox Copilot is replying"
      className="flex h-11 items-center gap-1 rounded-lg border border-slate-200 bg-white px-4 shadow-sm"
      role="status"
    >
      {DOTS.map((dot) => (
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted" key={dot} />
      ))}
    </div>
  );
}
