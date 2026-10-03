import type { ChatSettingsBarProps } from '../ChatSettingsBar/ChatSettingsBar.types';

export interface ChatComposerProps {
  settings: ChatSettingsBarProps['settings'];
  isAgentLocked: boolean;
  onSettingChange: ChatSettingsBarProps['onChange'];
  draft: string;
  onDraftChange: (draft: string) => void;
  canSend: boolean;
  onSend: () => void;
}
