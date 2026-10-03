import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { DEFAULT_SETTINGS } from '../../constants';
import { ChatComposer } from './ChatComposer';

const setup = (overrides: Partial<Parameters<typeof ChatComposer>[0]> = {}) => {
  const props = {
    settings: DEFAULT_SETTINGS,
    isAgentLocked: false,
    onSettingChange: vi.fn(),
    draft: 'Hello',
    onDraftChange: vi.fn(),
    canSend: true,
    onSend: vi.fn(),
    ...overrides,
  };
  render(<ChatComposer {...props} />);
  return props;
};

describe('ChatComposer', () => {
  it('sends on Enter', async () => {
    const props = setup();

    await userEvent.type(screen.getByRole('textbox', { name: 'Message' }), '{Enter}');

    expect(props.onSend).toHaveBeenCalled();
  });

  it('disables sending when not allowed', () => {
    setup({ canSend: false });

    expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  });

  it('locks the agent picker for existing conversations', () => {
    setup({ isAgentLocked: true });

    expect(screen.queryByRole('combobox', { name: 'Agent' })).not.toBeInTheDocument();
    expect(screen.getByText('Inbox agent')).toBeInTheDocument();
  });

  it('reports model changes', async () => {
    const props = setup();

    await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Model' }), 'haiku');

    expect(props.onSettingChange).toHaveBeenCalledWith('model', 'haiku');
  });
});
