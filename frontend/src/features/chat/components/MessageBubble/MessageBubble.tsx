import { Bot } from 'lucide-react';
import { Avatar } from '@/components';
import { cn } from '@/utils/cn';
import type { MessageBubbleProps } from './MessageBubble.types';

export function MessageBubble({ role, content, userInitial }: MessageBubbleProps) {
  const isUser = role === 'user';
  return (
    <div className={cn('flex items-start gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <Avatar>
          <Bot className="h-4 w-4" />
        </Avatar>
      )}
      {/* Model output is rendered as plain text, never as HTML. */}
      <div
        className={cn(
          'max-w-[82%] whitespace-pre-wrap rounded-lg px-4 py-3 text-sm leading-6 shadow-sm sm:max-w-[72%]',
          isUser ? 'bg-ink text-white' : 'border border-slate-200 bg-white text-ink-soft',
        )}
      >
        {content}
      </div>
      {isUser && <Avatar tone="warm">{userInitial}</Avatar>}
    </div>
  );
}
