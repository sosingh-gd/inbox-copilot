import type { ChatSettings } from '../../types';

export interface ChatSettingsBarProps {
  settings: ChatSettings;
  isAgentLocked: boolean;
  onChange: <K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) => void;
}
