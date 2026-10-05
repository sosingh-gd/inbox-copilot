import { queryOptions, useQuery } from '@tanstack/react-query';
import { api, unwrap } from '@/lib/http';
import type { ChatSettings } from '../types';

export const chatKeys = {
  list: ['chat', 'conversations'] as const,
  detail: (conversationId: string) => ['chat', 'conversation', conversationId] as const,
};

export const chatApi = {
  listConversations: (signal?: AbortSignal) =>
    unwrap(api.GET('/api/v1/chat/conversations', { signal })),

  getConversation: (conversationId: string, signal?: AbortSignal) =>
    unwrap(
      api.GET('/api/v1/chat/conversations/{conversation_id}', {
        params: { path: { conversation_id: conversationId } },
        signal,
      }),
    ),

  createConversation: (settings: ChatSettings) =>
    unwrap(api.POST('/api/v1/chat/conversations', { body: settings })),
};

export function useConversationsQuery() {
  return useQuery({
    queryKey: chatKeys.list,
    queryFn: ({ signal }) => chatApi.listConversations(signal),
  });
}

export function conversationQuery(conversationId: string) {
  return queryOptions({
    queryKey: chatKeys.detail(conversationId),
    queryFn: ({ signal }) => chatApi.getConversation(conversationId, signal),
    // A conversation only changes when we send a message, and useChat refetches after
    // every send. Refetching on window focus could wipe a reply while it is streaming.
    refetchOnWindowFocus: false,
  });
}

/** Loads one conversation with its messages. Does nothing while there is no id yet. */
export function useConversationQuery(conversationId: string | undefined) {
  return useQuery({
    ...conversationQuery(conversationId ?? ''),
    enabled: conversationId !== undefined,
  });
}
