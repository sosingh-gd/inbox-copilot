import { Spinner, StatusText } from '@/components';
import { useChatPanel } from '../../hooks/useChatPanel';
import { ChatComposer } from '../ChatComposer';
import { ConversationHeader } from '../ConversationHeader';
import { MessageList } from '../MessageList';
import type { ChatPanelProps } from './ChatPanel.types';

export function ChatPanel({ conversationId, onConversationStarted, userInitial }: ChatPanelProps) {
  const chat = useChatPanel(conversationId, onConversationStarted);

  const composer = (
    <ChatComposer
      canSend={chat.canSend}
      draft={chat.draft}
      isAgentLocked={chat.isAgentLocked}
      onDraftChange={chat.setDraft}
      onSend={chat.send}
      onSettingChange={chat.updateSetting}
      settings={chat.settings}
    />
  );

  if (conversationId === undefined) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center bg-slate-50/60 px-4 pb-16 sm:px-8">
        <div className="flex w-full max-w-3xl flex-col gap-3">
          {composer}
          {chat.runError && <StatusText tone="error">{chat.runError}</StatusText>}
        </div>
      </div>
    );
  }

  if (chat.loadError) {
    return (
      <div className="grid flex-1 place-items-center px-4">
        <StatusText tone="error">{chat.loadError}</StatusText>
      </div>
    );
  }

  return (
    <>
      <ConversationHeader
        agent={chat.settings.agent}
        isReplying={chat.isReplying}
        title={chat.title ?? 'New conversation'}
      />
      {chat.isLoading && chat.messages.length === 0 ? (
        <div className="grid flex-1 place-items-center text-ink-muted">
          <Spinner label="Loading conversation" />
        </div>
      ) : (
        <MessageList
          error={chat.runError}
          isTyping={chat.isTyping}
          messages={chat.messages}
          userInitial={userInitial}
        />
      )}
      <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-4 sm:px-8">
        <div className="mx-auto w-full max-w-3xl">{composer}</div>
      </div>
    </>
  );
}
