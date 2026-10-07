import { ChevronRight, DatabaseZap } from 'lucide-react';
import { cn } from '@/utils/cn';
import { CACHE_PARTS, type CachePart, INPUT_KINDS } from '../constants';
import type { InputSection, InputSectionKind, ModelCall } from '../types';
import { formatCount } from '../utils';

interface InputBreakdownProps {
  calls: ModelCall[];
}

/**
 * Everything a reply sent to Claude as input, call by call, to find what makes it expensive.
 * Each call's input token count is real; the split across its sections is estimated by size.
 * Below the split by kind, a striped bar shows how much of the input the prompt cache served.
 */
export function InputBreakdown({ calls }: InputBreakdownProps) {
  const totalInput = calls.reduce((sum, call) => sum + call.inputTokens, 0);
  const byKind = tokensByKind(calls.flatMap((call) => call.sections));
  const usedCache = calls.some((call) => call.promptCaching);

  return (
    <div className="w-full rounded-lg border border-slate-200 bg-white text-xs text-ink-soft shadow-sm">
      <div className="space-y-2 border-b border-slate-200 px-3 py-2">
        <p className="font-medium text-ink">
          {calls.length} Claude {calls.length === 1 ? 'call' : 'calls'} · {formatCount(totalInput)}{' '}
          input tokens
        </p>
        <ShareBar parts={byKind} total={totalInput} />
        <ul className="flex flex-wrap gap-x-3 gap-y-1">
          {byKind.map(({ kind, tokens }) => (
            <li className="inline-flex items-center gap-1.5 tabular-nums" key={kind}>
              <span className={cn('h-2 w-2 rounded-sm', INPUT_KINDS[kind].color)} />
              {INPUT_KINDS[kind].label} ≈{formatCount(tokens)} ({percent(tokens, totalInput)})
            </li>
          ))}
        </ul>
        <CacheSummary calls={calls} total={totalInput} usedCache={usedCache} />
      </div>
      <ol className="divide-y divide-slate-100">
        {calls.map((call, index) => (
          // Calls never change once saved, so their position is a stable key.
          <li key={index}>
            <CallDetails call={call} number={index + 1} />
          </li>
        ))}
      </ol>
    </div>
  );
}

/** The reply's input split into read from cache, written to cache and not cached. Real counts. */
function CacheSummary({
  calls,
  total,
  usedCache,
}: {
  calls: ModelCall[];
  total: number;
  usedCache: boolean;
}) {
  if (!usedCache) {
    return (
      <p className="flex items-center gap-1.5 rounded-md border border-dashed border-slate-300 px-2 py-1.5 text-ink-muted">
        <DatabaseZap className="h-3.5 w-3.5 shrink-0" />
        Prompt caching was off: every call paid full price for all of its input.
      </p>
    );
  }
  const split = cacheSplit(
    calls.reduce((sum, call) => sum + call.cacheReadTokens, 0),
    calls.reduce((sum, call) => sum + call.cacheWriteTokens, 0),
    total,
  );
  return (
    <div className="space-y-1.5 rounded-md border border-teal-200 bg-teal-50/50 px-2 py-1.5">
      <p className="flex items-center gap-1.5 font-medium text-teal-800">
        <DatabaseZap className="h-3.5 w-3.5 shrink-0" />
        Prompt cache
      </p>
      <CacheBar split={split} total={total} />
      <ul className="flex flex-wrap gap-x-3 gap-y-1">
        {split.map(({ part, tokens }) => (
          <li className="inline-flex items-center gap-1.5 tabular-nums" key={part}>
            <span className={cn('h-2.5 w-2.5 rounded-sm', CACHE_PARTS[part].color)} />
            <span className={CACHE_PARTS[part].text}>{CACHE_PARTS[part].label}</span>{' '}
            {formatCount(tokens)} ({percent(tokens, total)})
          </li>
        ))}
      </ul>
    </div>
  );
}

function CallDetails({ call, number }: { call: ModelCall; number: number }) {
  return (
    <details className="group">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 hover:bg-slate-50">
        <ChevronRight className="h-3.5 w-3.5 shrink-0 transition-transform group-open:rotate-90" />
        <span className="font-medium text-ink">
          {number}. {call.agent} agent · turn {call.turn}
        </span>
        <span className="text-ink-muted">{call.model}</span>
        <span className="ml-auto inline-flex items-center gap-2 tabular-nums text-ink-muted">
          <CallCacheBadge call={call} />
          <span>
            {formatCount(call.inputTokens)} in · {formatCount(call.outputTokens)} out
          </span>
        </span>
      </summary>
      <div className="space-y-1 px-3 pb-3">
        <ShareBar parts={call.sections} total={call.inputTokens} />
        {call.promptCaching && (
          <CacheBar
            split={cacheSplit(call.cacheReadTokens, call.cacheWriteTokens, call.inputTokens)}
            total={call.inputTokens}
          />
        )}
        <ul className="divide-y divide-slate-100 rounded-md border border-slate-200">
          {call.sections.map((section, index) => (
            <li key={index}>
              <SectionDetails section={section} total={call.inputTokens} />
            </li>
          ))}
        </ul>
      </div>
    </details>
  );
}

/** "⛁ 3,200 read · 400 written" for a call that used the cache, "cache off" otherwise. */
function CallCacheBadge({ call }: { call: ModelCall }) {
  if (!call.promptCaching) {
    return <span className="rounded border border-dashed border-slate-300 px-1">cache off</span>;
  }
  return (
    <span className="inline-flex items-center gap-1 rounded bg-teal-50 px-1 ring-1 ring-teal-200">
      <DatabaseZap aria-hidden="true" className="h-3 w-3 text-teal-700" />
      <span className={CACHE_PARTS.read.text}>{formatCount(call.cacheReadTokens)} read</span>
      {call.cacheWriteTokens > 0 && (
        <>
          <span aria-hidden="true">·</span>
          <span className={CACHE_PARTS.write.text}>
            {formatCount(call.cacheWriteTokens)} written
          </span>
        </>
      )}
    </span>
  );
}

function SectionDetails({ section, total }: { section: InputSection; total: number }) {
  // A section served whole from the cache gets a teal edge, so cached stretches stand out.
  const fullyCached = section.tokens > 0 && section.cacheReadTokens >= section.tokens;
  return (
    <details
      className={cn(
        'group/section border-l-2',
        fullyCached ? 'border-teal-400 bg-teal-50/40' : 'border-transparent',
      )}
    >
      <summary className="flex cursor-pointer list-none items-center gap-2 px-2 py-1.5 hover:bg-slate-50">
        <ChevronRight className="h-3 w-3 shrink-0 transition-transform group-open/section:rotate-90" />
        <span className={cn('h-2 w-2 shrink-0 rounded-sm', INPUT_KINDS[section.kind].color)} />
        <span className="min-w-0 truncate">
          <span className="text-ink-muted">{INPUT_KINDS[section.kind].label}</span> ·{' '}
          {section.label}
        </span>
        <span className="ml-auto inline-flex shrink-0 items-center gap-1.5 tabular-nums text-ink-muted">
          <CachePill part="read" tokens={section.cacheReadTokens} />
          <CachePill part="write" tokens={section.cacheWriteTokens} />
          <span>
            ≈{formatCount(section.tokens)} tok · {percent(section.tokens, total)} ·{' '}
            {formatCount(section.chars)} chars
          </span>
        </span>
      </summary>
      <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words border-t border-slate-100 bg-slate-50 px-2 py-1.5 font-mono text-[11px] leading-4">
        {section.text || '(empty)'}
      </pre>
    </details>
  );
}

/** A small striped tag with the section's estimated share read from or written to the cache. */
function CachePill({ part, tokens }: { part: CachePart; tokens: number }) {
  if (tokens === 0) return null;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full bg-white px-1.5 ring-1 ring-slate-200',
        CACHE_PARTS[part].text,
      )}
      title={`${CACHE_PARTS[part].label} (estimated)`}
    >
      <span className={cn('h-2 w-2 rounded-full', CACHE_PARTS[part].color)} />≈{formatCount(tokens)}{' '}
      {part === 'read' ? 'cached' : 'written'}
    </span>
  );
}

/** One horizontal bar split by kind, each part as wide as its share of the tokens. */
function ShareBar({
  parts,
  total,
}: {
  parts: { kind: InputSectionKind; tokens: number }[];
  total: number;
}) {
  if (total === 0) return null;
  return (
    <div className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100">
      {parts.map((part, index) => (
        <span
          className={INPUT_KINDS[part.kind].color}
          key={index}
          style={{ width: `${(part.tokens / total) * 100}%` }}
        />
      ))}
    </div>
  );
}

/** A taller, striped bar: read from cache, then written to it, then not cached. */
function CacheBar({
  split,
  total,
}: {
  split: { part: CachePart; tokens: number }[];
  total: number;
}) {
  if (total === 0) return null;
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-sm ring-1 ring-slate-200">
      {split.map(({ part, tokens }) => (
        <span
          className={CACHE_PARTS[part].color}
          key={part}
          style={{ width: `${(tokens / total) * 100}%` }}
          title={`${CACHE_PARTS[part].label}: ${formatCount(tokens)}`}
        />
      ))}
    </div>
  );
}

function cacheSplit(read: number, write: number, total: number) {
  return [
    { part: 'read' as const, tokens: read },
    { part: 'write' as const, tokens: write },
    { part: 'uncached' as const, tokens: Math.max(0, total - read - write) },
  ];
}

function tokensByKind(sections: InputSection[]): { kind: InputSectionKind; tokens: number }[] {
  const totals = new Map<InputSectionKind, number>();
  for (const section of sections) {
    totals.set(section.kind, (totals.get(section.kind) ?? 0) + section.tokens);
  }
  return [...totals]
    .map(([kind, tokens]) => ({ kind, tokens }))
    .sort((a, b) => b.tokens - a.tokens);
}

function percent(part: number, total: number): string {
  return total === 0 ? '0%' : `${Math.round((part / total) * 100)}%`;
}
