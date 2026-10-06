import { CircleCheck, CircleX, Wrench } from 'lucide-react';
import { Spinner } from '@/components';
import { cn } from '@/utils/cn';
import type { ToolPart } from '../types';
import { formatDuration, toolLabel } from '../utils';

interface ToolCallChipProps {
  part: ToolPart;
}

/** One tool call in a reply: a spinner while it runs, then whether it worked and how long. */
export function ToolCallChip({ part }: ToolCallChipProps) {
  const isRunning = part.ok === null;
  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border bg-white px-2.5 py-1 text-xs',
        part.ok === false ? 'border-red-200 text-red-700' : 'border-slate-200 text-ink-muted',
      )}
    >
      <Wrench className="h-3.5 w-3.5" />
      <span>{toolLabel(part.tool)}</span>
      {isRunning ? (
        <Spinner size="sm" />
      ) : (
        <>
          {part.ok ? (
            <CircleCheck aria-label="succeeded" className="h-3.5 w-3.5 text-emerald-600" />
          ) : (
            <CircleX aria-label="failed" className="h-3.5 w-3.5" />
          )}
          {part.durationMs !== null && (
            <span className="tabular-nums">{formatDuration(part.durationMs)}</span>
          )}
        </>
      )}
    </div>
  );
}
