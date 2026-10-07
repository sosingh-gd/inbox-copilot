import { ArrowRight, PiggyBank, Receipt, Send } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { CacheSavings as Savings } from '../utils';
import { formatCount, formatUsd } from '../utils';

interface CacheSavingsProps {
  savings: Savings;
  /** One short chip, with the details in its tooltip (for the conversation header). */
  compact?: boolean;
}

/**
 * What prompt caching did for a reply or a conversation: the input actually sent, what it
 * was billed as, and the estimated cost with and without the cache. Only shown where the
 * cache was used, so replies without caching look exactly as before.
 *
 * A first message can cost more than without caching: writing to the cache costs 1.25x, and
 * the saving comes on the next calls that read it back.
 */
export function CacheSavings({ savings, compact = false }: CacheSavingsProps) {
  const { sentInput, billedInput, costUsd, costWithoutCacheUsd } = savings;
  const inputSaved = sentInput === 0 ? 0 : Math.round((1 - billedInput / sentInput) * 100);
  const costSaved =
    costUsd !== null && costWithoutCacheUsd !== null ? costWithoutCacheUsd - costUsd : null;
  const isSaving = inputSaved >= 0;
  const tone = isSaving
    ? 'bg-teal-50 text-teal-800 ring-teal-200'
    : 'bg-orange-50 text-orange-800 ring-orange-200';
  const details =
    `Sent ${formatCount(sentInput)} input tokens, billed as about ${formatCount(billedInput)}.` +
    (costUsd !== null && costWithoutCacheUsd !== null
      ? ` Estimated ${formatUsd(costUsd)} instead of ${formatUsd(costWithoutCacheUsd)} without the cache.`
      : '');

  if (compact) {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 tabular-nums ring-1',
          tone,
        )}
        title={details}
      >
        <PiggyBank className="h-3.5 w-3.5" />
        {isSaving ? `Cache saved ≈${inputSaved}%` : `Cache cost +${-inputSaved}%`}
        {costSaved !== null && costSaved > 0 && <span>· ≈{formatUsd(costSaved)}</span>}
      </span>
    );
  }

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md px-2 py-1 text-xs tabular-nums ring-1',
        tone,
      )}
    >
      <span className="inline-flex items-center gap-1.5" title="Input tokens sent to Claude">
        <Send className="h-3.5 w-3.5" />
        Sent {formatCount(sentInput)} in
        <ArrowRight aria-hidden="true" className="h-3 w-3" />
        billed as ≈{formatCount(billedInput)}
        <span
          className={cn(
            'rounded px-1 font-semibold',
            isSaving ? 'bg-teal-600 text-white' : 'bg-orange-500 text-white',
          )}
        >
          {isSaving ? `−${inputSaved}%` : `+${-inputSaved}%`}
        </span>
      </span>
      {costUsd !== null && costWithoutCacheUsd !== null && (
        <span className="inline-flex items-center gap-1.5" title="Estimated from list prices">
          <Receipt className="h-3.5 w-3.5" />≈{formatUsd(costUsd)}
          <span className="opacity-60">
            instead of <s>{formatUsd(costWithoutCacheUsd)}</s>
          </span>
        </span>
      )}
      {costSaved !== null && (
        <span className="inline-flex items-center gap-1.5 font-medium">
          <PiggyBank className="h-3.5 w-3.5" />
          {costSaved >= 0
            ? `saved ≈${formatUsd(costSaved)}`
            : `≈${formatUsd(-costSaved)} extra to fill the cache`}
        </span>
      )}
    </div>
  );
}
