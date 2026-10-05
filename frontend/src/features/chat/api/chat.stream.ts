// Uses fetch directly because EventSource can't send a POST body.
import { createParser } from 'eventsource-parser';
import { env } from '@/config/env';
import { ApiError, defaultHeaders } from '@/lib/http';
import type { ChatEvent, ChatRunRequest } from '../types';

/**
 * Sends one message and calls `onText` with each piece of Claude's reply as it arrives.
 * Resolves when the reply is complete; throws if it fails or the connection drops.
 */
export async function streamChatRun(
  conversationId: string,
  body: ChatRunRequest,
  options: { signal: AbortSignal; onText: (text: string) => void },
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
