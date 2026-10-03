import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';
import { server } from '@/test/server';
import { renderWithProviders } from '@/test/utils';
import { chatHandlers } from '../../api/chat.mocks';
import { ConversationList } from './ConversationList';

describe('ConversationList', () => {
  it('lists conversations and reports the selected one', async () => {
    server.use(...chatHandlers);
    const onSelect = vi.fn();
    renderWithProviders(<ConversationList onNewConversation={vi.fn()} onSelect={onSelect} />);

    await userEvent.click(await screen.findByRole('button', { name: /design team follow-up/i }));

    expect(onSelect).toHaveBeenCalledWith('c1');
  });

  it('shows the API error message when loading fails', async () => {
    server.use(
      http.get('*/api/v1/chat/conversations', () =>
        HttpResponse.json(
          {
            type: 'about:blank',
            title: 'Bad Gateway',
            status: 502,
            code: 'x',
            detail: 'Upstream down',
          },
          { status: 502 },
        ),
      ),
    );
    renderWithProviders(<ConversationList onNewConversation={vi.fn()} onSelect={vi.fn()} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('Upstream down');
  });
});
