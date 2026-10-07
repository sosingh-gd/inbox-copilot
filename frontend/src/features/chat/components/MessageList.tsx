import { Fragment, useEffect, useRef } from 'react';
import { StatusText } from '@/components';
import type { ChatMessage } from '../types';
import { ContextSummary } from './ContextSummary';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: ChatMessage[];
  userInitial: string;
  error: string | null;
  /** What Claude sees instead of the messages up to `summarizedThrough`, if anything. */
  summary: string | null;
  summarizedThrough: string | null;
}

export function MessageList({
  messages,
  userInitial,
  error,
  summary,
  summarizedThrough,
}: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const lastParts = messages.at(-1)?.parts; // a new array on every streamed piece

  // Keep the newest message in view as messages arrive and the thinking and reply stream in.
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages.length, lastParts]);

  // The summary sits after the last message it replaced. Server timestamps are ISO 8601 in
  // UTC, but compared as dates in case their formats differ.
  const summaryIndex =
    summary && summarizedThrough
      ? messages.findLastIndex(
          (message) => new Date(message.createdAt) <= new Date(summarizedThrough),
        )
      : -1;
  const folded = summaryIndex + 1;

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 px-4 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        {messages.map((message, index) => (
          <Fragment key={message.id}>
            <MessageBubble message={message} userInitial={userInitial} />
            {index === summaryIndex && summary && (
              <ContextSummary messageCount={folded} summary={summary} />
            )}
          </Fragment>
        ))}
        {error && <StatusText tone="error">{error}</StatusText>}
        <div ref={endRef} />
      </div>
    </div>
  );
}
