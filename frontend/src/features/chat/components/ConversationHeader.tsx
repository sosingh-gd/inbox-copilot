import { cn } from '@/utils/cn';
import { AGENTS } from '../constants';
import type { AgentKind } from '../types';

interface ConversationHeaderProps {
  title: string;
  agent: AgentKind;
  isReplying: boolean;
}

export function ConversationHeader({ title, agent, isReplying }: ConversationHeaderProps) {
  return (
    <div className="flex h-16 shrink-0 items-center border-b border-slate-200 px-5 sm:px-8">
      <div className="min-w-0">
        <h1 className="truncate text-base font-semibold text-ink">{title}</h1>
        <p className="mt-0.5 text-xs text-ink-muted">{AGENTS[agent].label}</p>
      </div>
      <span
        className={cn(
          'ml-auto inline-flex items-center gap-2 text-xs font-medium',
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
  );
}
