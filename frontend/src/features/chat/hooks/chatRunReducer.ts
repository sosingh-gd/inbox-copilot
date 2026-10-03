import type { ChatEvent, ChatSettings } from '../types';

export interface ChatRunState {
  status: 'idle' | 'streaming' | 'done' | 'error';
  /** Undefined for a new conversation until the server sends run_started. */
  conversationId?: string;
  settings?: ChatSettings;
  userMessage?: string;
  userMessageId?: string;
  /** The assistant reply received so far. */
  text: string;
  messageId?: string;
  error?: string;
}

export type ChatRunAction =
  | { type: 'start'; conversationId?: string; settings: ChatSettings; userMessage: string }
  | { type: 'event'; event: ChatEvent }
  | { type: 'fail'; message: string };

export const initialChatRunState: ChatRunState = { status: 'idle', text: '' };

export function chatRunReducer(state: ChatRunState, action: ChatRunAction): ChatRunState {
  switch (action.type) {
    case 'start':
      return {
        status: 'streaming',
        text: '',
        conversationId: action.conversationId,
        settings: action.settings,
        userMessage: action.userMessage,
      };
    case 'fail':
      return { ...state, status: 'error', error: action.message };
    case 'event':
      return applyEvent(state, action.event);
  }
}

function applyEvent(state: ChatRunState, event: ChatEvent): ChatRunState {
  switch (event.type) {
    case 'run_started':
      return {
        ...state,
        conversationId: event.conversationId,
        userMessageId: event.userMessageId,
      };
    case 'text_delta':
      return { ...state, text: state.text + event.text };
    case 'run_completed':
      return { ...state, status: 'done', messageId: event.messageId };
    case 'run_failed':
      return { ...state, status: 'error', error: event.message };
    default: {
      const unhandled: never = event; // compile error if the backend adds an event type
      return unhandled;
    }
  }
}
