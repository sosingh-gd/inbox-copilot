import { MessageSquare, Trash2 } from 'lucide-react';
import { IconButton, Spinner, StatusText } from '@/components';
import { errorMessage } from '@/lib/http';
import { cn } from '@/utils/cn';
import { useDeleteFactMutation, useMemoryFactsQuery } from '../api/memory.api';
import { CATEGORIES } from '../constants';
import type { MemoryFact } from '../types';

interface MemoryFactListProps {
  onOpenConversation: (conversationId: string) => void;
}

/** Everything remembered about the user, with where each fact came from. */
export function MemoryFactList({ onOpenConversation }: MemoryFactListProps) {
  const facts = useMemoryFactsQuery();
  const deleteFact = useDeleteFactMutation();

  return (
    <div className="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 px-4 py-6 sm:px-8">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
        <div>
          <h1 className="text-lg font-semibold text-ink">Memory</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Facts remembered from chats saved to memory. Chats with “Use memory” on can draw on
            them. New facts are added when you start a chat that uses memory.
          </p>
        </div>

        {facts.isPending && (
          <div className="flex justify-center py-8 text-ink-muted">
            <Spinner label="Loading memory" />
          </div>
        )}
        {facts.isError && (
          <StatusText tone="error">
            {errorMessage(facts.error, 'Could not load memory.')}
          </StatusText>
        )}
        {deleteFact.isError && (
          <StatusText tone="error">
            {errorMessage(deleteFact.error, 'Could not forget that fact.')}
          </StatusText>
        )}
        {facts.data?.length === 0 && (
          <p className="rounded-lg border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-ink-muted">
            Nothing remembered yet.
          </p>
        )}

        {facts.data && facts.data.length > 0 && (
          <>
            <p className="text-xs text-ink-muted">
              {facts.data.length} {facts.data.length === 1 ? 'fact' : 'facts'}
            </p>
            <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white shadow-sm">
              {facts.data.map((fact) => (
                <li key={fact.id}>
                  <FactRow
                    fact={fact}
                    isDeleting={deleteFact.isPending && deleteFact.variables === fact.id}
                    onDelete={() => deleteFact.mutate(fact.id)}
                    onOpenConversation={() => onOpenConversation(fact.sourceConversationId)}
                  />
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

interface FactRowProps {
  fact: MemoryFact;
  isDeleting: boolean;
  onDelete: () => void;
  onOpenConversation: () => void;
}

function FactRow({ fact, isDeleting, onDelete, onOpenConversation }: FactRowProps) {
  const category = CATEGORIES[fact.category];
  return (
    <div className={cn('flex items-start gap-3 px-4 py-3', isDeleting && 'opacity-50')}>
      <div className="min-w-0 flex-1">
        <p className="text-sm text-ink">{fact.text}</p>
        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-muted">
          <span className={cn('rounded px-1.5 py-0.5 font-medium', category.className)}>
            {category.label}
          </span>
          <span>{new Date(fact.updatedAt).toLocaleDateString()}</span>
          <button
            className="inline-flex min-w-0 items-center gap-1 rounded hover:text-brand focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-200"
            onClick={onOpenConversation}
            title="Open the chat this came from"
            type="button"
          >
            <MessageSquare className="h-3.5 w-3.5 shrink-0" />
            <span className="truncate">{fact.sourceConversationTitle}</span>
          </button>
        </div>
      </div>
      <IconButton
        disabled={isDeleting}
        icon={<Trash2 className="h-4 w-4" />}
        label="Forget this fact"
        onClick={onDelete}
        size="sm"
      />
    </div>
  );
}
