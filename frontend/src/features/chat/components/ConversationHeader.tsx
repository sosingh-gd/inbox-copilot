import { cn } from '@/utils/cn';
import type { Usage } from '../types';
import { TokenCounts } from './TokenCounts';

interface ConversationHeaderProps {
  title: string;
  isReplying: boolean;
  /** Tokens used by the whole conversation, or null before its first reply. */
  usage: Usage | null;
}

export function ConversationHeader({ title, isReplying, usage }: ConversationHeaderProps) {
  return (
    <div className="flex h-16 shrink-0 items-center border-b border-slate-200 px-5 sm:px-8">
      <h1 className="min-w-0 truncate text-base font-semibold text-ink">{title}</h1>
      <div className="ml-auto flex shrink-0 items-center gap-4 pl-4 text-xs">
        {usage && (
          <span className="hidden text-ink-muted sm:inline-flex">
            <TokenCounts usage={usage} />
          </span>
        )}
        <span
          className={cn(
            'inline-flex items-center gap-2 font-medium',
            isReplying ? 'text-brand' : 'text-success',
          )}
        >
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              isReplying ? 'animate-pulse bg-brand' : 'bg-emerald-500',
            )}
          />
          {isReplying ? 'Replying' : 'Ready'}
        </span>
      </div>
    </div>
  );
}
