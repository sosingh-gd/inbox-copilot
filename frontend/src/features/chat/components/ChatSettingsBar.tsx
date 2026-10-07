import { BrainCircuit, Cpu, DatabaseZap, Gauge, History, Save } from 'lucide-react';
import { SegmentedControl, Select, Toggle } from '@/components';
import { cn } from '@/utils/cn';
import { CONTEXT_CAP_OPTIONS, MODEL_OPTIONS, REASONING_OPTIONS } from '../constants';
import type { ChatSettings } from '../types';
import { formatThousands } from '../utils';

export interface ChatSettingsBarProps {
  settings: ChatSettings;
  onChange: <K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) => void;
  /** True once the conversation exists: "use memory" can then no longer change. */
  isMemoryLocked: boolean;
  /** Estimated prompt tokens before the next message, or null for a new chat. */
  contextTokens: number | null;
}

export function ChatSettingsBar({
  settings,
  onChange,
  isMemoryLocked,
  contextTokens,
}: ChatSettingsBarProps) {
  const contextShare = contextTokens === null ? 0 : contextTokens / settings.contextCap;

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

      <div
        className="flex items-center gap-2"
        title="Near 80% of the cap, older messages are summarized and Claude sees the summary instead"
      >
        <Select
          aria-label="Context cap"
          icon={<Gauge className="h-4 w-4 text-indigo-700" />}
          onChange={(cap) => onChange('contextCap', Number(cap))}
          options={CONTEXT_CAP_OPTIONS}
          value={String(settings.contextCap)}
        />
        {contextTokens !== null && (
          <span
            className={cn(
              'text-xs tabular-nums',
              contextShare > 0.8 ? 'font-medium text-amber-700' : 'text-ink-muted',
            )}
          >
            ~{formatThousands(contextTokens)} / {formatThousands(settings.contextCap)}
          </span>
        )}
      </div>

      <Toggle
        checked={settings.promptCaching}
        hint={
          settings.promptCaching
            ? 'Unchanged input (tools, system prompt, earlier turns) is read back from the cache at a tenth of the price'
            : 'Every Claude call pays full price for all of its input. Turn on to compare.'
        }
        icon={<DatabaseZap className="h-4 w-4 text-teal-700" />}
        label="Prompt caching"
        onChange={(promptCaching) => onChange('promptCaching', promptCaching)}
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
