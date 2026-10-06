import { ArrowDown, ArrowUp, Coins, Database } from 'lucide-react';
import type { Usage } from '../types';
import { formatCount, inputTokensOf, totalTokensOf } from '../utils';

interface TokenCountsProps {
  usage: Usage;
}

/**
 * "1,364 tokens (↓1,125 in · ↑239 out) · 800 cached", used per message and for the whole
 * conversation. Cached tokens are the part of the input that was read from the prompt cache.
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
      <Database className="h-3.5 w-3.5" />
      <span>{formatCount(usage.cacheReadTokens)} cached</span>
    </span>
  );
}
