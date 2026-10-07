import { ChevronRight } from 'lucide-react';
import { cn } from '@/utils/cn';
import { INPUT_KINDS } from '../constants';
import type { InputSection, InputSectionKind, ModelCall } from '../types';
import { formatCount } from '../utils';

interface InputBreakdownProps {
  calls: ModelCall[];
}

/**
 * Everything a reply sent to Claude as input, call by call, to find what makes it expensive.
 * Each call's input token count is real; the split across its sections is estimated by size.
 */
export function InputBreakdown({ calls }: InputBreakdownProps) {
  const totalInput = calls.reduce((sum, call) => sum + call.inputTokens, 0);
  const byKind = tokensByKind(calls.flatMap((call) => call.sections));

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

function CallDetails({ call, number }: { call: ModelCall; number: number }) {
  return (
    <details className="group">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 hover:bg-slate-50">
        <ChevronRight className="h-3.5 w-3.5 shrink-0 transition-transform group-open:rotate-90" />
        <span className="font-medium text-ink">
          {number}. {call.agent} agent · turn {call.turn}
        </span>
        <span className="text-ink-muted">{call.model}</span>
        <span className="ml-auto tabular-nums text-ink-muted">
          {formatCount(call.inputTokens)} in
          {call.cacheReadTokens > 0 && ` (${formatCount(call.cacheReadTokens)} cached)`} ·{' '}
          {formatCount(call.outputTokens)} out
        </span>
      </summary>
      <div className="space-y-1 px-3 pb-3">
        <ShareBar parts={call.sections} total={call.inputTokens} />
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

function SectionDetails({ section, total }: { section: InputSection; total: number }) {
  return (
    <details className="group/section">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-2 py-1.5 hover:bg-slate-50">
        <ChevronRight className="h-3 w-3 shrink-0 transition-transform group-open/section:rotate-90" />
        <span className={cn('h-2 w-2 shrink-0 rounded-sm', INPUT_KINDS[section.kind].color)} />
        <span className="min-w-0 truncate">
          <span className="text-ink-muted">{INPUT_KINDS[section.kind].label}</span> ·{' '}
          {section.label}
        </span>
        <span className="ml-auto shrink-0 tabular-nums text-ink-muted">
          ≈{formatCount(section.tokens)} tok · {percent(section.tokens, total)} ·{' '}
          {formatCount(section.chars)} chars
        </span>
      </summary>
      <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words border-t border-slate-100 bg-slate-50 px-2 py-1.5 font-mono text-[11px] leading-4">
        {section.text || '(empty)'}
      </pre>
    </details>
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
