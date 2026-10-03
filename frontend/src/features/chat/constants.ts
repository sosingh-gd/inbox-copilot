import { Bot, CalendarDays, Inbox, type LucideIcon } from 'lucide-react';
import type { AgentKind, ChatSettings, ModelChoice, ReasoningLevel } from './types';

// Records keyed by the generated union types: if the backend adds a value, these stop compiling
// until it gets a label here.
export const AGENTS: Record<AgentKind, { label: string; icon: LucideIcon }> = {
  inbox: { label: 'Inbox agent', icon: Inbox },
  calendar: { label: 'Calendar agent', icon: CalendarDays },
  general: { label: 'General assistant', icon: Bot },
};

const MODEL_LABELS: Record<ModelChoice, string> = {
  sonnet: 'Claude Sonnet',
  haiku: 'Claude Haiku',
};

const REASONING_LABELS: Record<ReasoningLevel, string> = {
  fast: 'Fast',
  balanced: 'Balanced',
  deep: 'Deep',
};

const toOptions = <T extends string>(labels: Record<T, string>) =>
  (Object.keys(labels) as T[]).map((value) => ({ value, label: labels[value] }));

export const AGENT_OPTIONS = (Object.keys(AGENTS) as AgentKind[]).map((value) => ({
  value,
  label: AGENTS[value].label,
}));
export const MODEL_OPTIONS = toOptions(MODEL_LABELS);
export const REASONING_OPTIONS = toOptions(REASONING_LABELS);

export const DEFAULT_SETTINGS: ChatSettings = {
  agent: 'inbox',
  model: 'sonnet',
  reasoning: 'balanced',
};
