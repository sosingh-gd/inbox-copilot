import { Bot } from 'lucide-react';
import { Avatar, Markdown } from '@/components';
import { cn } from '@/utils/cn';
import type { ChatMessage, MessagePart } from '../types';
import { isLiveReply } from '../utils';
import { MessageStats } from './MessageStats';
import { ThinkingBlock } from './ThinkingBlock';
import { ToolCallChip } from './ToolCallChip';
import { TypingIndicator } from './TypingIndicator';

interface MessageBubbleProps {
  message: ChatMessage;
  userInitial: string;
}

export function MessageBubble({ message, userInitial }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isLive = isLiveReply(message);
  // Claude's replies are thinking and text in the order produced; the user's is just text.
  const parts: MessagePart[] = message.parts ?? [{ type: 'text', text: message.content }];

  return (
    <div className={cn('flex items-start gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <Avatar>
          <Bot className="h-4 w-4" />
        </Avatar>
      )}
      <div
        className={cn(
          'flex max-w-[82%] flex-col gap-2 sm:max-w-[72%]',
          isUser ? 'items-end' : 'items-start',
        )}
      >
        {!isUser && <MessageStats message={message} />}
        {parts.length === 0 && <TypingIndicator />}
        {parts.map((part, index) => {
          // Parts are only ever appended, so their position is a stable key.
          switch (part.type) {
            case 'thinking':
              return (
                <ThinkingBlock
                  // A thinking block is done once anything follows it, or the reply has finished.
                  isDone={!isLive || index < parts.length - 1}
                  key={index}
                  thinking={part.text}
                />
              );
            case 'tool':
              return <ToolCallChip key={index} part={part} />;
            case 'note':
              return (
                <p className="whitespace-pre-wrap px-1 text-xs italic text-ink-muted" key={index}>
                  {part.text}
                </p>
              );
            case 'text':
              // Claude's text is Markdown (rendered without raw HTML); the user's is plain text.
              return (
                <div
                  className={cn(
                    'max-w-full rounded-lg px-4 py-3 text-sm leading-6 shadow-sm',
                    isUser
                      ? 'whitespace-pre-wrap bg-ink text-white'
                      : 'border border-slate-200 bg-white text-ink-soft',
                  )}
                  key={index}
                >
                  {isUser ? part.text : <Markdown>{part.text}</Markdown>}
                </div>
              );
          }
        })}
      </div>
      {isUser && <Avatar tone="warm">{userInitial}</Avatar>}
    </div>
  );
}
