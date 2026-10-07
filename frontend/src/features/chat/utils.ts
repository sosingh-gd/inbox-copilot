import { LIVE_REPLY_ID } from './constants';
import type { ChatMessage, ChatSettings, MessagePart, ModelCall, Usage } from './types';

export function settingsOf(source: ChatSettings): ChatSettings {
  return {
    model: source.model,
    reasoning: source.reasoning,
    promptCaching: source.promptCaching,
    useMemory: source.useMemory,
    saveToMemory: source.saveToMemory,
  };
}

const DAY_MS = 24 * 60 * 60 * 1000;

/** Short, sidebar-friendly timestamp: "Now", "3:41 PM", "Yesterday", "Mon", "Sep 12". */
export function formatUpdatedAt(iso: string, now: Date = new Date()): string {
  const date = new Date(iso);
  if (now.getTime() - date.getTime() < 60_000) return 'Now';

  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const time = date.getTime();
  if (time >= startOfToday) {
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }
  if (time >= startOfToday - DAY_MS) return 'Yesterday';
  if (time >= startOfToday - 6 * DAY_MS) return date.toLocaleDateString([], { weekday: 'short' });
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

/** "4.2s" under a minute, "1m 05s" after. */
export function formatDuration(ms: number): string {
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const whole = Math.floor(seconds);
  return `${Math.floor(whole / 60)}m ${String(whole % 60).padStart(2, '0')}s`;
}

export function formatCount(count: number): string {
  return count.toLocaleString();
}

/** All input tokens: Anthropic counts cached input apart from `inputTokens`. */
export function inputTokensOf(usage: Usage): number {
  return usage.inputTokens + usage.cacheReadTokens + usage.cacheWriteTokens;
}

export function totalTokensOf(usage: Usage): number {
  return inputTokensOf(usage) + usage.outputTokens;
}

/** The conversation's token totals so far, including a reply that is still streaming. */
export function totalUsageOf(messages: ChatMessage[]): Usage | null {
  const usages = messages.flatMap((message) => (message.usage ? [message.usage] : []));
  if (usages.length === 0) return null;
  return usages.reduce((total, usage) => ({
    inputTokens: total.inputTokens + usage.inputTokens,
    outputTokens: total.outputTokens + usage.outputTokens,
    cacheReadTokens: total.cacheReadTokens + usage.cacheReadTokens,
    cacheWriteTokens: total.cacheWriteTokens + usage.cacheWriteTokens,
  }));
}

/** What prompt caching changed for a set of Claude calls. All but `sentInput` are estimates. */
export interface CacheSavings {
  /** Input tokens actually sent to Claude, cached or not. */
  sentInput: number;
  /** The same input, counted as if every token were charged at the normal input price. */
  billedInput: number;
  /** US dollars; null when a call's model has no known prices. */
  costUsd: number | null;
  costWithoutCacheUsd: number | null;
}

/** Savings for these calls, or null when none of them read from or wrote to the cache. */
export function cacheSavingsOf(calls: ModelCall[]): CacheSavings | null {
  if (!calls.some((call) => call.cacheReadTokens + call.cacheWriteTokens > 0)) return null;
  const sum = (value: (call: ModelCall) => number) =>
    calls.reduce((total, call) => total + value(call), 0);
  const hasPrices = calls.every((call) => call.costUsd !== null);
  return {
    sentInput: sum((call) => call.inputTokens),
    billedInput: sum((call) => call.billedInputTokens),
    costUsd: hasPrices ? sum((call) => call.costUsd ?? 0) : null,
    costWithoutCacheUsd: hasPrices ? sum((call) => call.costWithoutCacheUsd ?? 0) : null,
  };
}

/** Savings over every saved reply in the conversation. */
export function conversationSavingsOf(messages: ChatMessage[]): CacheSavings | null {
  return cacheSavingsOf(messages.flatMap((message) => message.calls ?? []));
}

/** "$0.0039": four decimals, since one reply costs a fraction of a cent. */
export function formatUsd(amount: number): string {
  return amount > 0 && amount < 0.0001 ? '<$0.0001' : `$${amount.toFixed(4)}`;
}

/** True for the reply that is still streaming in. */
export function isLiveReply(message: ChatMessage): boolean {
  return message.id === LIVE_REPLY_ID;
}

/**
 * Adds a streamed piece of thinking or text: it extends the last part when that is the same
 * kind, and starts a new part when Claude switches between thinking and writing.
 */
export function appendToParts(
  parts: MessagePart[],
  type: 'thinking' | 'text',
  text: string,
): MessagePart[] {
  const last = parts.at(-1);
  return last?.type === type
    ? [...parts.slice(0, -1), { type, text: last.text + text }]
    : [...parts, { type, text }];
}

/**
 * Adds a running tool call. Text written just before it was progress ("I'll check your
 * calendar"), so it becomes a note; the server stores it the same way.
 */
export function startToolPart(parts: MessagePart[], agent: string, tool: string): MessagePart[] {
  const last = parts.at(-1);
  const earlier =
    last?.type === 'text' ? [...parts.slice(0, -1), { ...last, type: 'note' as const }] : parts;
  return [...earlier, { type: 'tool', agent, tool, ok: null, durationMs: null }];
}

/** Marks the running call of `tool` as finished. */
export function finishToolPart(
  parts: MessagePart[],
  tool: string,
  ok: boolean,
  durationMs: number,
): MessagePart[] {
  const index = parts.findLastIndex((part) => part.type === 'tool' && part.tool === tool);
  return parts.map((part, i) => (i === index ? { ...part, ok, durationMs } : part));
}

/** "ask_calendar_agent" -> "Asked the calendar agent"; other tools keep their own name. */
export function toolLabel(tool: string): string {
  const agent = /^ask_(.+)_agent$/.exec(tool)?.[1];
  return agent ? `Asked the ${agent.replaceAll('_', ' ')} agent` : tool.replaceAll('_', ' ');
}
