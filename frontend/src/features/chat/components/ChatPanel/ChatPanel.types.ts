export interface ChatPanelProps {
  /** Undefined shows the "new conversation" composer. */
  conversationId?: string;
  /** Called when sending the first message has created a conversation. */
  onConversationStarted: (conversationId: string) => void;
  userInitial: string;
}
