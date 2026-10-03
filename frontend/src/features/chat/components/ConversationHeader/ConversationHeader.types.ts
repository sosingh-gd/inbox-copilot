import type { AgentKind } from '../../types';

export interface ConversationHeaderProps {
  title: string;
  agent: AgentKind;
  isReplying: boolean;
}
