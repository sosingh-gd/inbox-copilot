import { describe, expect, it } from 'vitest';
import { DEFAULT_SETTINGS } from '../constants';
import type { ChatEvent } from '../types';
import { chatRunReducer, initialChatRunState, type ChatRunState } from './chatRunReducer';

const play = (events: ChatEvent[]): ChatRunState =>
  events.reduce(
    (state, event) => chatRunReducer(state, { type: 'event', event }),
    chatRunReducer(initialChatRunState, {
      type: 'start',
      settings: DEFAULT_SETTINGS,
      userMessage: 'Hello',
    }),
  );

describe('chatRunReducer', () => {
  it('accumulates text and finishes on run_completed', () => {
    const state = play([
      { type: 'run_started', conversationId: 'c1', userMessageId: 'u1' },
      { type: 'text_delta', text: 'Hi ' },
      { type: 'text_delta', text: 'there' },
      { type: 'run_completed', messageId: 'a1', usage: null },
    ]);

    expect(state).toMatchObject({
      status: 'done',
      conversationId: 'c1',
      userMessageId: 'u1',
      text: 'Hi there',
      messageId: 'a1',
    });
  });

  it('records the server message on run_failed', () => {
    const state = play([
      { type: 'run_started', conversationId: 'c1', userMessageId: 'u1' },
      { type: 'run_failed', code: 'refused', message: 'Claude declined to answer this request.' },
    ]);

    expect(state.status).toBe('error');
    expect(state.error).toBe('Claude declined to answer this request.');
  });

  it('resets everything when a new run starts', () => {
    const finished = play([{ type: 'text_delta', text: 'old' }]);

    const restarted = chatRunReducer(finished, {
      type: 'start',
      conversationId: 'c2',
      settings: DEFAULT_SETTINGS,
      userMessage: 'Next',
    });

    expect(restarted).toMatchObject({ status: 'streaming', text: '', conversationId: 'c2' });
  });
});
