import { MessageSquare, Plus } from 'lucide-react';
import { IconButton, Spinner, StatusText } from '@/components';
import { errorMessage } from '@/lib/http';
import { cn } from '@/utils/cn';
import { useConversationsQuery } from '../api/chat.api';
import { formatUpdatedAt } from '../utils';

interface ConversationListProps {
  activeConversationId?: string;
  onSelect: (conversationId: string) => void;
  onNewConversation: () => void;
}

export function ConversationList({
  activeConversationId,
  onSelect,
  onNewConversation,
}: ConversationListProps) {
  const conversations = useConversationsQuery();

  return (
    <>
      <div className="flex items-center justify-between px-4 pb-3 pt-5">
        <h2 className="text-sm font-semibold text-ink">Chats</h2>
        <IconButton
          icon={<Plus className="h-4 w-4" />}
          label="New conversation"
          onClick={onNewConversation}
          size="sm"
          variant="primary"
        />
      </div>

      <nav aria-label="Conversations" className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        {conversations.isPending && (
          <div className="flex justify-center py-6 text-ink-muted">
            <Spinner label="Loading conversations" />
          </div>
        )}
        {conversations.isError && (
          <div className="px-2">
            <StatusText tone="error">
              {errorMessage(conversations.error, 'Could not load conversations.')}
            </StatusText>
          </div>
        )}
        {conversations.data?.length === 0 && (
          <p className="px-3 py-2 text-sm text-ink-muted">No conversations yet.</p>
        )}
        <ul className="space-y-1">
          {conversations.data?.map((conversation) => {
            const isActive = conversation.id === activeConversationId;
            return (
              <li key={conversation.id}>
                <button
                  aria-current={isActive ? 'page' : undefined}
                  className={cn(
                    'flex w-full items-start gap-3 rounded-md px-3 py-3 text-left transition',
                    isActive ? 'bg-blue-50 text-brand-deep' : 'text-ink-soft hover:bg-slate-100',
                  )}
                  onClick={() => onSelect(conversation.id)}
                  type="button"
                >
                  <MessageSquare className="mt-0.5 h-4 w-4 shrink-0" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium">{conversation.title}</span>
                    <span className="mt-1 block text-xs text-ink-muted">
                      {formatUpdatedAt(conversation.updatedAt)}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
