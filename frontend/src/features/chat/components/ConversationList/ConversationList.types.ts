export interface ConversationListProps {
  activeConversationId?: string;
  onSelect: (conversationId: string) => void;
  onNewConversation: () => void;
}
