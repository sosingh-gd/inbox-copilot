import type { DisplayMessage } from '../../types';

export interface MessageBubbleProps {
  role: DisplayMessage['role'];
  content: string;
  userInitial: string;
}
