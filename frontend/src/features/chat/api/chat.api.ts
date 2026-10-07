import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, unwrap } from '@/lib/http';
import type { ChatSettings, ConversationDetail, ConversationSummary } from '../types';

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

  updateConversation: (conversationId: string, saveToMemory: boolean) =>
    unwrap(
      api.PATCH('/api/v1/chat/conversations/{conversation_id}', {
        params: { path: { conversation_id: conversationId } },
        body: { saveToMemory },
      }),
    ),
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

/** Turns "save to memory" on or off. Turning it off forgets the facts the chat added. */
export function useUpdateConversationMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      conversationId,
      saveToMemory,
    }: {
      conversationId: string;
      saveToMemory: boolean;
    }) => chatApi.updateConversation(conversationId, saveToMemory),
    onSuccess: (updated: ConversationSummary) => {
      queryClient.setQueryData<ConversationDetail>(chatKeys.detail(updated.id), (cached) =>
        cached ? { ...cached, ...updated } : cached,
      );
      void queryClient.invalidateQueries({ queryKey: chatKeys.list });
    },
  });
}

/** Loads one conversation with its messages. Does nothing while there is no id yet. */
export function useConversationQuery(conversationId: string | undefined) {
  return useQuery({
    ...conversationQuery(conversationId ?? ''),
    enabled: conversationId !== undefined,
  });
}
