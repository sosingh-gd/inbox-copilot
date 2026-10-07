import type { ChatSettings, InputSectionKind, ModelChoice, ReasoningLevel } from './types';

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

/** How each kind of input is named and colored in the input breakdown. */
export const INPUT_KINDS: Record<InputSectionKind, { label: string; color: string }> = {
  system: { label: 'System prompt', color: 'bg-sky-500' },
  memory: { label: 'Memory', color: 'bg-fuchsia-500' },
  tool_definition: { label: 'Tool definitions', color: 'bg-amber-500' },
  text: { label: 'Conversation text', color: 'bg-slate-500' },
  thinking: { label: 'Thinking', color: 'bg-violet-500' },
  tool_use: { label: 'Tool calls', color: 'bg-emerald-500' },
  tool_result: { label: 'Tool results', color: 'bg-rose-500' },
};

/**
 * How input is split by the prompt cache in the input breakdown. Striped, unlike the solid
 * kind colors, so the two bars are not read as one.
 */
export const CACHE_PARTS = {
  read: {
    label: 'Read from cache',
    color:
      'bg-[repeating-linear-gradient(135deg,var(--color-teal-500)_0_3px,var(--color-teal-300)_3px_6px)]',
    text: 'text-teal-700',
  },
  write: {
    label: 'Written to cache',
    color:
      'bg-[repeating-linear-gradient(135deg,var(--color-orange-400)_0_3px,var(--color-orange-200)_3px_6px)]',
    text: 'text-orange-700',
  },
  uncached: { label: 'Not cached', color: 'bg-slate-300', text: 'text-ink-muted' },
} as const;

export type CachePart = keyof typeof CACHE_PARTS;

const toOptions = <T extends string>(labels: Record<T, string>) =>
  (Object.keys(labels) as T[]).map((value) => ({ value, label: labels[value] }));

export const MODEL_OPTIONS = toOptions(MODEL_LABELS);
export const REASONING_OPTIONS = toOptions(REASONING_LABELS);

export const DEFAULT_SETTINGS: ChatSettings = {
  model: 'sonnet',
  reasoning: 'balanced',
  promptCaching: true,
  useMemory: true,
  saveToMemory: true,
};

/** The id of the reply that is still streaming; saved replies have server ids. */
export const LIVE_REPLY_ID = 'temporary-reply';
