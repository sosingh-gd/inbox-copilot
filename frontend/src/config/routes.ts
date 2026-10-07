/** Every route path lives here, so links never hard-code URLs. */
export const paths = {
  home: '/',
  login: '/login',
  chats: '/chats',
  chat: (conversationId: string) => `/chats/${encodeURIComponent(conversationId)}`,
  memory: '/memory',
} as const;

/** The main sections, linked from the app header. */
export const navItems = [
  { label: 'Chats', to: paths.chats },
  { label: 'Memory', to: paths.memory },
] as const;
