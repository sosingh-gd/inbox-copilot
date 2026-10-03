import { http, HttpResponse } from 'msw';
import type { ConversationDetail, ConversationSummary } from '../types';

// Typed with generated types: a backend schema change breaks these at compile time.
export const conversationFixture: ConversationSummary = {
  id: 'c1',
  title: 'Design team follow-up',
  agent: 'inbox',
  model: 'sonnet',
  reasoning: 'balanced',
  updatedAt: '2026-10-02T09:00:00Z',
};

export const conversationDetailFixture: ConversationDetail = {
  ...conversationFixture,
  messages: [
    { id: 'm1', role: 'user', content: 'Draft a follow-up', createdAt: '2026-10-02T09:00:00Z' },
    { id: 'm2', role: 'assistant', content: 'Hi team…', createdAt: '2026-10-02T09:00:05Z' },
  ],
};

export const chatHandlers = [
  http.get('*/api/v1/chat/conversations', () => HttpResponse.json([conversationFixture])),
  http.get('*/api/v1/chat/conversations/:conversationId', () =>
    HttpResponse.json(conversationDetailFixture),
  ),
];
