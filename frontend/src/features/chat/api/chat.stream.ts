// POST + fetch streaming: EventSource can't send a request body.
import { createParser, type EventSourceMessage } from 'eventsource-parser';
import { env } from '@/config/env';
import { ApiError, defaultHeaders } from '@/lib/http';
import type { ChatEvent, ChatRunRequest } from '../types';

const TERMINAL = new Set<ChatEvent['type']>(['run_completed', 'run_failed']);

export async function streamChatRun(
  body: ChatRunRequest,
  options: { signal: AbortSignal; onEvent: (event: ChatEvent) => void },
): Promise<void> {
  const res = await fetch(`${env.apiBaseUrl}/api/v1/chat/runs/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...defaultHeaders(),
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  // Errors before the stream starts (auth, validation, unknown conversation) are Problem Details.
  if (!res.ok || !res.body) throw await ApiError.fromResponse(res);

  let sawTerminal = false;
  const parser = createParser({
    onEvent(message: EventSourceMessage) {
      const event = JSON.parse(message.data) as ChatEvent;
      if (TERMINAL.has(event.type)) sawTerminal = true;
      options.onEvent(event);
    },
  });

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    parser.feed(value);
  }
  if (!sawTerminal && !options.signal.aborted) {
    throw new Error('The connection dropped before the reply finished.');
  }
}
