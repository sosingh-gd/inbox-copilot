import type { ChatSettings, ModelChoice, ReasoningLevel } from './types';

// Records keyed by the generated union types: if the backend adds a value, these stop compiling
// until it gets a label here.
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

export const MODEL_OPTIONS = toOptions(MODEL_LABELS);
export const REASONING_OPTIONS = toOptions(REASONING_LABELS);

export const DEFAULT_SETTINGS: ChatSettings = {
  model: 'sonnet',
  reasoning: 'balanced',
};

/** The id of the reply that is still streaming; saved replies have server ids. */
export const LIVE_REPLY_ID = 'temporary-reply';
