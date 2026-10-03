import { api, unwrap } from '@/lib/http';

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
};
