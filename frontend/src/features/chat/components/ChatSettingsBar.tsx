import { BrainCircuit, Cpu, History, Save } from 'lucide-react';
import { SegmentedControl, Select, Toggle } from '@/components';
import { MODEL_OPTIONS, REASONING_OPTIONS } from '../constants';
import type { ChatSettings } from '../types';

export interface ChatSettingsBarProps {
  settings: ChatSettings;
  onChange: <K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) => void;
  /** True once the conversation exists: "use memory" can then no longer change. */
  isMemoryLocked: boolean;
}

export function ChatSettingsBar({ settings, onChange, isMemoryLocked }: ChatSettingsBarProps) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <Select
        aria-label="Model"
        icon={<Cpu className="h-4 w-4 text-emerald-700" />}
        onChange={(model) => onChange('model', model)}
        options={MODEL_OPTIONS}
        value={settings.model}
      />

      <SegmentedControl
        aria-label="Reasoning"
        icon={<BrainCircuit className="mr-1 h-4 w-4 text-violet-700" />}
        onChange={(reasoning) => onChange('reasoning', reasoning)}
        options={REASONING_OPTIONS}
        value={settings.reasoning}
      />

      <Toggle
        checked={settings.useMemory}
        disabled={isMemoryLocked}
        hint={
          isMemoryLocked
            ? 'Set when the chat starts'
            : 'Replies can use what was remembered from earlier chats'
        }
        icon={<History className="h-4 w-4 text-fuchsia-700" />}
        label="Use memory"
        onChange={(useMemory) => onChange('useMemory', useMemory)}
      />

      <Toggle
        checked={settings.saveToMemory}
        hint={
          settings.saveToMemory
            ? 'Later chats can use facts from this one. Turn off to forget them.'
            : 'Nothing from this chat is remembered'
        }
        icon={<Save className="h-4 w-4 text-sky-700" />}
        label="Save to memory"
        onChange={(saveToMemory) => onChange('saveToMemory', saveToMemory)}
      />
    </div>
  );
}
