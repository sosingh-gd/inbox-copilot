import { useKeyedState } from '@/hooks/useKeyedState';
import { errorMessage, isApiError } from '@/lib/http';
import { useConversationQuery } from '../api/chat.queries';
import { DEFAULT_SETTINGS } from '../constants';
import type { ChatSettings } from '../types';
import { settingsOf, withRunMessages } from '../utils';
import { initialChatRunState } from './chatRunReducer';
import { useChatRun } from './useChatRun';

/** Everything the chat panel shows and does, for the selected (or a new) conversation. */
export function useChatPanel(
  conversationId: string | undefined,
  onConversationStarted: (conversationId: string) => void,
) {
  const conversation = useConversationQuery(conversationId);
  const { state: run, start } = useChatRun({ onConversationStarted });

  // The run may belong to another conversation if the user switched while it streamed.
  const activeRun = run.conversationId === conversationId ? run : initialChatRunState;
  const isReplying = run.status === 'streaming';

  const key = conversationId ?? 'new';
  const savedSettings = conversation.data ? settingsOf(conversation.data) : activeRun.settings;
  const [settings, setSettings] = useKeyedState<ChatSettings>(
    key,
    savedSettings ?? DEFAULT_SETTINGS,
  );
  const [draft, setDraft] = useKeyedState(key, '');

  const isAgentLocked = conversationId !== undefined;
  const canSend = draft.trim().length > 0 && !isReplying;

  const updateSetting = <K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) => {
    if (name === 'agent' && isAgentLocked) return;
    setSettings({ ...settings, [name]: value });
  };

  const send = () => {
    if (!canSend) return;
    const content = draft.trim();
    setDraft('');
    void start({ conversationId: conversationId ?? null, content, ...settings });
  };

  const loadError = conversation.error
    ? isApiError(conversation.error) && conversation.error.status === 404
      ? 'This conversation does not exist.'
      : errorMessage(conversation.error, 'Could not load this conversation.')
    : undefined;

  return {
    title: conversation.data?.title,
    isLoading: conversation.isLoading,
    loadError,
    messages: withRunMessages(conversation.data?.messages ?? [], activeRun),
    isTyping: activeRun.status === 'streaming' && activeRun.text === '',
    runError: activeRun.status === 'error' ? activeRun.error : undefined,
    isReplying,
    settings,
    isAgentLocked,
    updateSetting,
    draft,
    setDraft,
    canSend,
    send,
  };
}
