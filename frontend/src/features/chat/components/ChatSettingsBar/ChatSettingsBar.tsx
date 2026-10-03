import { BrainCircuit, Cpu, LockKeyhole } from 'lucide-react';
import { SegmentedControl, Select } from '@/components';
import { AGENT_OPTIONS, AGENTS, MODEL_OPTIONS, REASONING_OPTIONS } from '../../constants';
import type { ChatSettingsBarProps } from './ChatSettingsBar.types';

export function ChatSettingsBar({ settings, isAgentLocked, onChange }: ChatSettingsBarProps) {
  const AgentIcon = AGENTS[settings.agent].icon;
  const agentIcon = <AgentIcon className="h-4 w-4 text-brand" />;

  return (
    <div className="mb-3 flex flex-wrap items-center gap-2">
      {isAgentLocked ? (
        <div
          className="flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 text-sm text-ink"
          title="The agent is fixed for this conversation"
        >
          {agentIcon}
          <span className="font-medium">{AGENTS[settings.agent].label}</span>
          <LockKeyhole aria-label="Locked" className="h-3.5 w-3.5 text-ink-muted" />
        </div>
      ) : (
        <Select
          aria-label="Agent"
          icon={agentIcon}
          onChange={(agent) => onChange('agent', agent)}
          options={AGENT_OPTIONS}
          value={settings.agent}
        />
      )}

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
