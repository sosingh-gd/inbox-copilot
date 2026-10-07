import type { FactCategory } from './types';

// Keyed by the generated union: if the backend adds a category, this stops compiling until it
// gets a label here.
export const CATEGORIES: Record<FactCategory, { label: string; className: string }> = {
  preference: { label: 'Preference', className: 'bg-sky-50 text-sky-800' },
  person: { label: 'Person', className: 'bg-emerald-50 text-emerald-800' },
  commitment: { label: 'Commitment', className: 'bg-amber-50 text-amber-800' },
  deadline: { label: 'Deadline', className: 'bg-rose-50 text-rose-800' },
  other: { label: 'Other', className: 'bg-slate-100 text-slate-700' },
};
