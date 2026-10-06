import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { MarkdownProps } from './Markdown.types';

// Compact styles sized for chat text. Block code gets a dark panel; inline code a light chip.
const components: Components = {
  p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
  h1: ({ children }) => (
    <h3 className="mb-2 mt-4 text-base font-semibold text-ink first:mt-0">{children}</h3>
  ),
  h2: ({ children }) => (
    <h3 className="mb-2 mt-4 text-base font-semibold text-ink first:mt-0">{children}</h3>
  ),
  h3: ({ children }) => <h4 className="mb-1 mt-3 font-semibold text-ink first:mt-0">{children}</h4>,
  h4: ({ children }) => <h4 className="mb-1 mt-3 font-semibold text-ink first:mt-0">{children}</h4>,
  ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  a: ({ children, href }) => (
    <a className="text-brand underline" href={href} rel="noopener noreferrer" target="_blank">
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-slate-300 pl-3 text-ink-muted">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-3 border-slate-200" />,
  code: ({ children }) => (
    <code className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[0.85em]">{children}</code>
  ),
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded-md bg-slate-900 p-3 text-xs text-slate-100 [&_code]:bg-transparent [&_code]:p-0">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="my-2 overflow-x-auto">
      <table className="w-full border-collapse text-xs">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border border-slate-200 bg-slate-50 px-2 py-1 text-left font-semibold">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="border border-slate-200 px-2 py-1 align-top">{children}</td>,
};

/**
 * Renders Markdown (with GitHub tables, task lists and strikethrough) safely: raw HTML is not
 * rendered, links open in a new tab, and images are dropped to their alt text so content can't
 * load remote resources (such as tracking pixels from quoted emails).
 */
export function Markdown({ children }: MarkdownProps) {
  return (
    <div className="min-w-0 break-words">
      <ReactMarkdown
        components={components}
        disallowedElements={['img']}
        remarkPlugins={[remarkGfm]}
        unwrapDisallowed
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
