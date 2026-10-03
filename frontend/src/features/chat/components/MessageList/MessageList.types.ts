import type { DisplayMessage } from '../../types';

export interface MessageListProps {
  messages: DisplayMessage[];
  isTyping: boolean;
  userInitial: string;
  error?: string;
}
