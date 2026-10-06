import { BrainCircuit, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/cn';

interface ThinkingBlockProps {
  thinking: string;
  /** False while Claude is still writing this block. Once done, it collapses unless the user
      has opened or closed it. */
  isDone: boolean;
}

/** One stretch of Claude's summarized reasoning, shown as plain text. */
export function ThinkingBlock({ thinking, isDone }: ThinkingBlockProps) {
  const [chosenOpen, setChosenOpen] = useState<boolean | null>(null);
  const isOpen = chosenOpen ?? !isDone;

  return (
    <div className="w-full rounded-lg border border-violet-200 bg-violet-50/60 text-xs">
      <button
        aria-expanded={isOpen}
        className="flex w-full items-center gap-1.5 px-3 py-2 font-medium text-violet-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300"
        onClick={() => setChosenOpen(!isOpen)}
        type="button"
      >
        <BrainCircuit className={cn('h-3.5 w-3.5', !isDone && 'animate-pulse')} />
        {isDone ? 'Thought process' : 'Thinking…'}
        <ChevronDown
          className={cn('ml-auto h-3.5 w-3.5 transition-transform', isOpen && 'rotate-180')}
        />
      </button>
      {isOpen && (
        <div className="max-h-64 overflow-y-auto whitespace-pre-wrap border-t border-violet-200 px-3 py-2 leading-5 text-ink-muted">
          {thinking}
        </div>
      )}
    </div>
  );
}
