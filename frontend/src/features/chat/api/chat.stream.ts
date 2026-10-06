// Uses fetch directly because EventSource can't send a POST body.
import { createParser } from 'eventsource-parser';
import { env } from '@/config/env';
import { ApiError, defaultHeaders } from '@/lib/http';
import type { ChatEvent, ChatRunRequest, Usage } from '../types';

interface StreamHandlers {
  signal: AbortSignal;
  /** A piece of Claude's reply. */
  onText: (text: string) => void;
  /** A piece of Claude's summarized reasoning. */
  onThinking: (text: string) => void;
  /** Running token totals for this message, sub-agents included. */
  onUsage: (usage: Usage) => void;
  /** Claude called a tool; the reply continues once `onToolFinished` follows. */
  onToolStarted: (agent: string, tool: string) => void;
  onToolFinished: (tool: string, ok: boolean, durationMs: number) => void;
  /** The reply is saved; `durationMs` is how long the server took. */
  onCompleted: (durationMs: number) => void;
}

/**
 * Sends one message and calls the handlers as Claude's thinking, reply and token totals arrive.
 * Resolves when the reply is complete; throws if it fails or the connection drops.
 */
export async function streamChatRun(
  conversationId: string,
  body: ChatRunRequest,
  options: StreamHandlers,
): Promise<void> {
  const url = `${env.apiBaseUrl}/api/v1/chat/conversations/${encodeURIComponent(conversationId)}/stream`;
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...defaultHeaders() },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  // Problems found before streaming starts (not signed in, bad input) come back as a
  // normal error response.
  if (!res.ok || !res.body) throw await ApiError.fromResponse(res);

  let lastEvent: ChatEvent | undefined;
  const parser = createParser({
    onEvent(message) {
      const event = JSON.parse(message.data) as ChatEvent;
      lastEvent = event;
      if (event.type === 'text_delta') options.onText(event.text);
      else if (event.type === 'thinking_delta') options.onThinking(event.text);
      else if (event.type === 'usage_updated') options.onUsage(event.usage);
      else if (event.type === 'tool_started') options.onToolStarted(event.agent, event.tool);
      else if (event.type === 'tool_finished') {
        options.onToolFinished(event.tool, event.ok, event.durationMs);
      } else if (event.type === 'run_completed') options.onCompleted(event.durationMs);
    },
  });

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    parser.feed(value);
  }

  // The server always ends with run_completed or run_failed.
  if (lastEvent?.type === 'run_failed') throw new Error(lastEvent.message);
  if (lastEvent?.type !== 'run_completed') {
    throw new Error('The connection dropped before the reply finished.');
  }
}
