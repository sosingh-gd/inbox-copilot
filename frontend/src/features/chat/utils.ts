import type { ChatSettings } from './types';

export function settingsOf(source: ChatSettings): ChatSettings {
  return { agent: source.agent, model: source.model, reasoning: source.reasoning };
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
