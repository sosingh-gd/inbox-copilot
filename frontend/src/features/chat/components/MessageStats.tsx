import { Timer } from 'lucide-react';
import { useElapsedMs } from '../hooks/useElapsedMs';
import type { ChatMessage } from '../types';
import { formatDuration, isLiveReply } from '../utils';
import { TokenCounts } from './TokenCounts';

interface MessageStatsProps {
  message: ChatMessage;
}

/**
 * Time and tokens for one reply: live while it streams, then the saved values. Replies saved
 * before these were recorded have neither, so they show nothing.
 */
export function MessageStats({ message }: MessageStatsProps) {
  const isRunning = isLiveReply(message);
  const { durationMs } = message;
  if (!isRunning && durationMs === null && !message.usage) return null;

  return (
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
    </div>
  );
}

function LiveDuration({ startedAt }: { startedAt: string }) {
  const elapsedMs = useElapsedMs(Date.parse(startedAt));
  return <span className="text-brand">{formatDuration(elapsedMs)}</span>;
}
