import { ChevronDown, ScrollText } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/cn';

interface ContextSummaryProps {
  summary: string;
  /** How many messages above it replaces for Claude. */
  messageCount: number;
}

/**
 * The line between messages Claude now sees only as a summary and the ones it still sees word
 * for word. The messages above stay on screen; opening it shows what Claude gets instead.
 */
export function ContextSummary({ summary, messageCount }: ContextSummaryProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="flex flex-col gap-2">
      <button
        aria-expanded={isOpen}
        className="flex items-center gap-3 text-xs font-medium text-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-300"
        onClick={() => setIsOpen(!isOpen)}
        type="button"
      >
        <span className="h-px flex-1 bg-indigo-200" />
        <ScrollText className="h-3.5 w-3.5" />
        Claude sees the {messageCount} message{messageCount === 1 ? '' : 's'} above as a summary
        <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', isOpen && 'rotate-180')} />
        <span className="h-px flex-1 bg-indigo-200" />
      </button>
      {isOpen && (
        <div className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-lg border border-indigo-200 bg-indigo-50/60 px-4 py-3 text-xs leading-5 text-ink-muted">
          {summary}
        </div>
      )}
    </div>
  );
}
