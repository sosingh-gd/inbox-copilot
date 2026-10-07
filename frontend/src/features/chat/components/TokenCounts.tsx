import { ArrowDown, ArrowUp, Coins, DatabaseZap } from 'lucide-react';
import { cn } from '@/utils/cn';
import { CACHE_PARTS } from '../constants';
import type { Usage } from '../types';
import { formatCount, inputTokensOf, totalTokensOf } from '../utils';

interface TokenCountsProps {
  usage: Usage;
}

/**
 * "1,364 tokens (↓1,125 in · ↑239 out) · 800 cached · 300 written to cache", used per message
 * and for the whole conversation. Cached tokens are the part of the input read from the prompt
 * cache; written tokens were stored in it for later calls.
 */
export function TokenCounts({ usage }: TokenCountsProps) {
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5 tabular-nums">
      <Coins className="h-3.5 w-3.5" />
      <span>{formatCount(totalTokensOf(usage))} tokens</span>
      <span className="inline-flex items-center gap-1">
        (<ArrowDown aria-hidden="true" className="h-3 w-3" />
        <span>{formatCount(inputTokensOf(usage))} in</span>
        <span aria-hidden="true">·</span>
        <ArrowUp aria-hidden="true" className="h-3 w-3" />
        <span>{formatCount(usage.outputTokens)} out</span>)
      </span>
      <span aria-hidden="true">·</span>
      <span
        className={cn(
          'inline-flex items-center gap-1',
          usage.cacheReadTokens > 0 && CACHE_PARTS.read.text,
        )}
      >
        <DatabaseZap className="h-3.5 w-3.5" />
        {formatCount(usage.cacheReadTokens)} cached
      </span>
      {usage.cacheWriteTokens > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span className={CACHE_PARTS.write.text}>
            {formatCount(usage.cacheWriteTokens)} written to cache
          </span>
        </>
      )}
    </span>
  );
}
