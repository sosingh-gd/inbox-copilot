import { Spinner, StatusText } from '@/components';
import { errorMessage, isApiError } from '@/lib/http';
import { useChat } from '../hooks/useChat';
import { ChatComposer } from './ChatComposer';
import { ConversationHeader } from './ConversationHeader';
import { MessageList } from './MessageList';

interface ChatPanelProps {
  /** Leave undefined for a new chat. */
  conversationId?: string;
  /** Called after the first reply of a new chat, once it has a conversation id. */
  onConversationCreated: (conversationId: string) => void;
  userInitial: string;
}

export function ChatPanel({ conversationId, onConversationCreated, userInitial }: ChatPanelProps) {
  const chat = useChat(conversationId, onConversationCreated);

  const composer = (
    <ChatComposer
      canSend={chat.canSend}
      draft={chat.draft}
      isMemoryLocked={chat.isMemoryLocked}
      onDraftChange={chat.setDraft}
      onSend={chat.send}
      onSettingChange={chat.changeSetting}
      settings={chat.settings}
    />
  );

  // New chat: just the composer, centered.
  if (!chat.hasConversation) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center bg-slate-50/60 px-4 pb-16 sm:px-8">
        <div className="flex w-full max-w-3xl flex-col gap-3">
          {composer}
          {chat.error && <StatusText tone="error">{chat.error}</StatusText>}
        </div>
      </div>
    );
  }

  if (chat.loadError) {
    const message =
      isApiError(chat.loadError) && chat.loadError.status === 404
        ? 'This conversation does not exist.'
        : errorMessage(chat.loadError, 'Could not load this conversation.');
    return (
      <div className="grid flex-1 place-items-center px-4">
        <StatusText tone="error">{message}</StatusText>
      </div>
    );
  }

  return (
    <>
      <ConversationHeader
        isReplying={chat.isReplying}
        title={chat.title ?? ''}
        usage={chat.totalUsage}
      />
      {chat.isLoading ? (
        <div className="grid flex-1 place-items-center text-ink-muted">
          <Spinner label="Loading conversation" />
        </div>
      ) : (
        <MessageList error={chat.error} messages={chat.messages} userInitial={userInitial} />
      )}
      <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-4 sm:px-8">
        <div className="mx-auto w-full max-w-3xl">{composer}</div>
      </div>
    </>
  );
}
