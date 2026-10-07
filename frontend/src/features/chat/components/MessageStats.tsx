import { ChevronDown, ListTree, Timer } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/cn';
import { useElapsedMs } from '../hooks/useElapsedMs';
import type { ChatMessage } from '../types';
import { cacheSavingsOf, formatDuration, isLiveReply } from '../utils';
import { CacheSavings } from './CacheSavings';
import { InputBreakdown } from './InputBreakdown';
import { TokenCounts } from './TokenCounts';

interface MessageStatsProps {
  message: ChatMessage;
}

/**
 * Time and tokens for one reply: live while it streams, then the saved values. Replies saved
 * before these were recorded have neither, so they show nothing. Saved replies can also open
 * a breakdown of everything that was sent to Claude as input, and replies that used the prompt
 * cache show what it saved.
 */
export function MessageStats({ message }: MessageStatsProps) {
  const [showInput, setShowInput] = useState(false);
  const isRunning = isLiveReply(message);
  const { durationMs, calls } = message;
  if (!isRunning && durationMs === null && !message.usage) return null;
  const savings = calls ? cacheSavingsOf(calls) : null;

  return (
    <>
      <div className="flex flex-wrap items-center gap-3 px-1 text-xs text-ink-muted tabular-nums">
        {(isRunning || durationMs !== null) && (
          <span className="inline-flex items-center gap-1.5">
            <Timer className="h-3.5 w-3.5" />
            {durationMs === null ? (
              <LiveDuration startedAt={message.createdAt} />
            ) : (
              formatDuration(durationMs)
            )}
          </span>
        )}
        {message.usage ? (
          <TokenCounts usage={message.usage} />
        ) : (
          isRunning && <span>Counting tokens…</span>
        )}
        {calls && calls.length > 0 && (
          <button
            aria-expanded={showInput}
            className="inline-flex items-center gap-1 rounded px-1 font-medium text-brand hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-200"
            onClick={() => setShowInput(!showInput)}
            type="button"
          >
            <ListTree className="h-3.5 w-3.5" />
            Input breakdown
            <ChevronDown
              className={cn('h-3.5 w-3.5 transition-transform', showInput && 'rotate-180')}
            />
          </button>
        )}
      </div>
      {savings && <CacheSavings savings={savings} />}
      {showInput && calls && <InputBreakdown calls={calls} />}
    </>
  );
}

function LiveDuration({ startedAt }: { startedAt: string }) {
  const elapsedMs = useElapsedMs(Date.parse(startedAt));
  return <span className="text-brand">{formatDuration(elapsedMs)}</span>;
}
