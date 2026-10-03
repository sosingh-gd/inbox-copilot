export const chatKeys = {
  all: ['chat'] as const,
  lists: () => [...chatKeys.all, 'conversations'] as const,
  detail: (conversationId: string) => [...chatKeys.all, 'conversation', conversationId] as const,
};
