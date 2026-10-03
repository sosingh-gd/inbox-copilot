import { describe, expect, it } from 'vitest';
import { conversationDetailFixture } from './api/chat.mocks';
import { initialChatRunState, type ChatRunState } from './hooks/chatRunReducer';
import { formatUpdatedAt, withRunMessages } from './utils';

const persisted = conversationDetailFixture.messages;

describe('withRunMessages', () => {
  it('shows the pending user message and the streamed reply', () => {
    const run: ChatRunState = { status: 'streaming', userMessage: 'Next?', text: 'Partial' };

    expect(withRunMessages(persisted, run).map((m) => m.content)).toEqual([
      'Draft a follow-up',
      'Hi team…',
      'Next?',
      'Partial',
    ]);
  });

  it('drops pending copies once the server returns them', () => {
    const run: ChatRunState = {
      status: 'done',
      userMessage: 'Draft a follow-up',
      userMessageId: 'm1',
      text: 'Hi team…',
      messageId: 'm2',
    };

    expect(withRunMessages(persisted, run)).toHaveLength(2);
  });

  it('hides the user message of a run the server rejected', () => {
    const run: ChatRunState = { status: 'error', userMessage: 'Rejected', text: '', error: 'x' };

    expect(withRunMessages([], run)).toEqual([]);
  });

  it('returns persisted messages when idle', () => {
    expect(withRunMessages(persisted, initialChatRunState)).toHaveLength(2);
  });
});

describe('formatUpdatedAt', () => {
  const now = new Date('2026-10-03T15:00:00');

  it('labels very recent updates as Now', () => {
    expect(formatUpdatedAt('2026-10-03T14:59:30', now)).toBe('Now');
  });

  it('labels the previous day as Yesterday', () => {
    expect(formatUpdatedAt('2026-10-02T09:00:00', now)).toBe('Yesterday');
  });
});
