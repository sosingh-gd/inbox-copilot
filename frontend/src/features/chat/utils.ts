import type { ChatRunState } from './hooks/chatRunReducer';
import type { ChatMessage, ChatSettings, DisplayMessage } from './types';

export function settingsOf(source: ChatSettings): ChatSettings {
  return { agent: source.agent, model: source.model, reasoning: source.reasoning };
}

/**
 * Persisted messages plus the in-flight run's messages that the server hasn't returned yet.
 * Once a refetch includes them (matched by id), the pending copies disappear.
 */
export function withRunMessages(persisted: ChatMessage[], run: ChatRunState): DisplayMessage[] {
  const savedIds = new Set(persisted.map((message) => message.id));
  const messages: DisplayMessage[] = persisted.map(({ id, role, content }) => ({
    id,
    role,
    content,
  }));

  const userSaved = run.userMessageId !== undefined && savedIds.has(run.userMessageId);
  // A run that failed before the server accepted it never saved the user's message.
  const userAccepted = run.status !== 'error' || run.userMessageId !== undefined;
  if (run.userMessage && !userSaved && userAccepted) {
    messages.push({ id: 'pending-user', role: 'user', content: run.userMessage });
  }

  const replySaved = run.messageId !== undefined && savedIds.has(run.messageId);
  if (run.text && !replySaved) {
    messages.push({ id: 'pending-assistant', role: 'assistant', content: run.text });
  }
  return messages;
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
