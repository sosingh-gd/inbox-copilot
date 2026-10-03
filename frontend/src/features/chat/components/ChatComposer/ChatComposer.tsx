import { Send } from 'lucide-react';
import type { KeyboardEvent } from 'react';
import { IconButton, TextArea } from '@/components';
import { ChatSettingsBar } from '../ChatSettingsBar';
import type { ChatComposerProps } from './ChatComposer.types';

export function ChatComposer({
  settings,
  isAgentLocked,
  onSettingChange,
  draft,
  onDraftChange,
  canSend,
  onSend,
}: ChatComposerProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends, Shift+Enter adds a new line.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  return (
    <div className="w-full">
      <ChatSettingsBar
        isAgentLocked={isAgentLocked}
        onChange={onSettingChange}
        settings={settings}
      />
      <div className="flex items-end gap-3 rounded-lg border border-slate-300 bg-white p-2 shadow-sm focus-within:border-brand focus-within:ring-4 focus-within:ring-blue-100">
        <TextArea
          aria-label="Message"
          onChange={onDraftChange}
          onKeyDown={handleKeyDown}
          placeholder="Message Inbox Copilot"
          value={draft}
        />
        <IconButton
          disabled={!canSend}
          icon={<Send className="h-4 w-4" />}
          label="Send message"
          onClick={onSend}
          variant="primary"
        />
      </div>
    </div>
  );
}
