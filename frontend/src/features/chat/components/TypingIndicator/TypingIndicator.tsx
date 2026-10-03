import { Bot } from 'lucide-react';
import { Avatar } from '@/components';

const DOTS = ['first', 'second', 'third'] as const;

export function TypingIndicator() {
  return (
    <div className="flex items-start gap-3" role="status" aria-label="Inbox Copilot is replying">
      <Avatar>
        <Bot className="h-4 w-4" />
      </Avatar>
      <div className="flex h-11 items-center gap-1 rounded-lg border border-slate-200 bg-white px-4 shadow-sm">
        {DOTS.map((dot) => (
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-muted" key={dot} />
        ))}
      </div>
    </div>
  );
}
