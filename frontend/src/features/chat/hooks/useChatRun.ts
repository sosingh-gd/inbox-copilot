import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useReducer, useRef } from 'react';
import { errorMessage } from '@/lib/http';
import { chatKeys } from '../api/chat.keys';
import { streamChatRun } from '../api/chat.stream';
import type { ChatRunRequest } from '../types';
import { chatRunReducer, initialChatRunState } from './chatRunReducer';

interface UseChatRunOptions {
  /** Called once the server has created a new conversation. */
  onConversationStarted?: (conversationId: string) => void;
}

/**
 * Streams one assistant reply. Streams don't fit the query cache, so progress lives in a
 * reducer; persisted conversations are refetched when the run ends.
 */
export function useChatRun({ onConversationStarted }: UseChatRunOptions = {}) {
  const [state, dispatch] = useReducer(chatRunReducer, initialChatRunState);
  const abortRef = useRef<AbortController | null>(null);
  const onStartedRef = useRef(onConversationStarted);
  const queryClient = useQueryClient();

  useEffect(() => {
    onStartedRef.current = onConversationStarted;
  }, [onConversationStarted]);

  useEffect(() => () => abortRef.current?.abort(), []); // abort on unmount

  const start = useCallback(
    async (request: ChatRunRequest) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      let conversationId = request.conversationId ?? undefined;
      const { agent, model, reasoning, content } = request;
      dispatch({
        type: 'start',
        conversationId,
        settings: { agent, model, reasoning },
        userMessage: content,
      });

      try {
        await streamChatRun(request, {
          signal: controller.signal,
          onEvent: (event) => {
            dispatch({ type: 'event', event });
            if (event.type === 'run_started' && conversationId === undefined) {
              conversationId = event.conversationId;
              void queryClient.invalidateQueries({ queryKey: chatKeys.lists() });
              onStartedRef.current?.(event.conversationId);
            }
          },
        });
      } catch (err) {
        // A newer run replaced this one, or the component unmounted: nothing to report.
        if (abortRef.current !== controller || controller.signal.aborted) return;
        dispatch({ type: 'fail', message: errorMessage(err, 'The reply failed.') });
      } finally {
        void queryClient.invalidateQueries({ queryKey: chatKeys.lists() });
        if (conversationId) {
          void queryClient.invalidateQueries({ queryKey: chatKeys.detail(conversationId) });
        }
      }
    },
    [queryClient],
  );

  return { state, start };
}
