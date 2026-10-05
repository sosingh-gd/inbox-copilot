import { useEffect, useRef } from 'react';
import { StatusText } from '@/components';
import type { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
  userInitial: string;
  error: string | null;
}

export function MessageList({ messages, isTyping, userInitial, error }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const lastContent = messages.at(-1)?.content;

  // Keep the newest message in view as messages arrive and the reply streams in.
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [messages.length, lastContent, isTyping]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 px-4 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        {messages.map((message) => (
          <MessageBubble
            content={message.content}
            key={message.id}
            role={message.role}
            userInitial={userInitial}
          />
        ))}
        {isTyping && <TypingIndicator />}
        {error && <StatusText tone="error">{error}</StatusText>}
        <div ref={endRef} />
      </div>
    </div>
  );
}
