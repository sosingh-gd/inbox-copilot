/** Every route path lives here, so links never hard-code URLs. */
export const paths = {
  home: '/',
  login: '/login',
  chats: '/chats',
  chat: (conversationId: string) => `/chats/${encodeURIComponent(conversationId)}`,
} as const;
