import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { errorMessage } from '@/lib/http';
import { chatApi, chatKeys, useConversationQuery } from '../api/chat.api';
import { streamChatRun } from '../api/chat.stream';
import { DEFAULT_SETTINGS } from '../constants';
import type { ChatMessage, ChatSettings, ConversationDetail } from '../types';
import { settingsOf } from '../utils';

/**
 * Everything the chat panel needs for one conversation, or for a new chat when
 * `conversationId` is undefined.
 *
 * How sending works:
 * 1. A new chat first creates its conversation on the server.
 * 2. The user's message and Claude's reply (as it streams in) are written straight into the
 *    cached conversation, so the screen always reads messages from one place.
 * 3. When the reply ends, the conversation is refetched and the saved messages replace the
 *    temporary ones.
 */
export function useChat(
  conversationId: string | undefined,
  onConversationCreated: (conversationId: string) => void,
) {
  const queryClient = useQueryClient();

  // A new chat gets its id when the first message is sent. If that reply fails we stay on
  // this page, so the retry goes to the same conversation.
  const [createdId, setCreatedId] = useState<string>();
  const activeId = conversationId ?? createdId;
  const conversation = useConversationQuery(activeId);

  // Settings come from the conversation until the user changes them.
  const [chosenSettings, setChosenSettings] = useState<ChatSettings | null>(null);
  const settings =
    chosenSettings ?? (conversation.data ? settingsOf(conversation.data) : DEFAULT_SETTINGS);
  const isAgentLocked = activeId !== undefined; // the agent can't change once a chat exists

  const [draft, setDraft] = useState('');
  const [isReplying, setIsReplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stop streaming if the user leaves this conversation.
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  const messages = conversation.data?.messages ?? [];
  const lastMessage = messages.at(-1);

  function changeSetting<K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) {
    if (name === 'agent' && isAgentLocked) return;
    setChosenSettings({ ...settings, [name]: value });
  }

  function updateCachedMessages(id: string, update: (messages: ChatMessage[]) => ChatMessage[]) {
    queryClient.setQueryData<ConversationDetail>(chatKeys.detail(id), (cached) =>
      cached ? { ...cached, messages: update(cached.messages) } : cached,
    );
  }

  async function send() {
    const content = draft.trim();
    if (!content || isReplying) return;

    const controller = new AbortController();
    abortRef.current = controller;
    setDraft('');
    setError(null);
    setIsReplying(true);

    let id = activeId;
    let succeeded = false;
    try {
      if (id === undefined) {
        const created = await chatApi.createConversation(settings);
        id = created.id;
        queryClient.setQueryData<ConversationDetail>(chatKeys.detail(id), {
          ...created,
          messages: [],
        });
        setCreatedId(id);
      }
      const conversationKey = id;
      // Make sure no older fetch lands on top of the messages we're about to add.
      await queryClient.cancelQueries({ queryKey: chatKeys.detail(conversationKey) });
      updateCachedMessages(conversationKey, (current) => [
        ...current,
        temporaryMessage('user', content),
      ]);

      await streamChatRun(
        conversationKey,
        { content, model: settings.model, reasoning: settings.reasoning },
        {
          signal: controller.signal,
          onText: (text) =>
            updateCachedMessages(conversationKey, (current) => appendToReply(current, text)),
        },
      );
      succeeded = true;
    } catch (err) {
      // An abort means the user left this conversation, so there's no one to tell.
      if (!controller.signal.aborted) setError(errorMessage(err, 'The reply failed.'));
    }

    // Swap the temporary messages for the saved ones, and refresh the sidebar.
    if (id !== undefined) {
      void queryClient.invalidateQueries({ queryKey: chatKeys.detail(id) });
    }
    void queryClient.invalidateQueries({ queryKey: chatKeys.list });
    setIsReplying(false);

    // A new chat moves to its own page once the first reply has arrived.
    if (id !== undefined && conversationId === undefined && succeeded) {
      onConversationCreated(id);
    }
  }

  return {
    hasConversation: activeId !== undefined,
    title: conversation.data?.title,
    isLoading: conversation.isLoading,
    loadError: conversation.error,
    messages,
    isTyping: isReplying && lastMessage?.role === 'user', // waiting for the first words
    isReplying,
    error,
    settings,
    isAgentLocked,
    changeSetting,
    draft,
    setDraft,
    canSend: draft.trim() !== '' && !isReplying,
    send,
  };
}

const TEMPORARY_REPLY_ID = 'temporary-reply';

function temporaryMessage(role: ChatMessage['role'], content: string): ChatMessage {
  const id = role === 'user' ? 'temporary-user' : TEMPORARY_REPLY_ID;
  return { id, role, content, createdAt: new Date().toISOString() };
}

/** Adds streamed text to the reply in progress, starting it on the first piece of text. */
function appendToReply(messages: ChatMessage[], text: string): ChatMessage[] {
  const last = messages.at(-1);
  if (last?.id === TEMPORARY_REPLY_ID) {
    return [...messages.slice(0, -1), { ...last, content: last.content + text }];
  }
  return [...messages, temporaryMessage('assistant', text)];
}
