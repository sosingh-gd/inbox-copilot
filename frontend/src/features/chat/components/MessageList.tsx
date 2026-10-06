import { useEffect, useRef } from 'react';
import { StatusText } from '@/components';
import type { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: ChatMessage[];
  userInitial: string;
  error: string | null;
}

export function MessageList({ messages, userInitial, error }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const lastParts = messages.at(-1)?.parts; // a new array on every streamed piece

  // Keep the newest message in view as messages arrive and the thinking and reply stream in.
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages.length, lastParts]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 px-4 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} userInitial={userInitial} />
        ))}
        {error && <StatusText tone="error">{error}</StatusText>}
        <div ref={endRef} />
      </div>
    </div>
  );
}
