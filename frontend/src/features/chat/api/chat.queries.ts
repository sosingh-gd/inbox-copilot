import { skipToken, useQuery } from '@tanstack/react-query';
import { chatApi } from './chat.api';
import { chatKeys } from './chat.keys';

export function useConversationsQuery() {
  return useQuery({
    queryKey: chatKeys.lists(),
    queryFn: ({ signal }) => chatApi.listConversations(signal),
  });
}

/** Loads a conversation with its messages; idle when no conversation is selected. */
export function useConversationQuery(conversationId: string | undefined) {
  return useQuery({
    queryKey: chatKeys.detail(conversationId ?? ''),
    queryFn: conversationId
      ? ({ signal }) => chatApi.getConversation(conversationId, signal)
      : skipToken,
  });
}
