import { BrainCircuit, Cpu } from 'lucide-react';
import { SegmentedControl, Select } from '@/components';
import { MODEL_OPTIONS, REASONING_OPTIONS } from '../constants';
import type { ChatSettings } from '../types';

export interface ChatSettingsBarProps {
  settings: ChatSettings;
  onChange: <K extends keyof ChatSettings>(name: K, value: ChatSettings[K]) => void;
}

export function ChatSettingsBar({ settings, onChange }: ChatSettingsBarProps) {
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
    </div>
  );
}
