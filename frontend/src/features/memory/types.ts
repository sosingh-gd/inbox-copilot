import type { components } from '@/lib/api/schema';

// Domain names for the generated API types. Never hand-write shapes the backend defines.
type Schemas = components['schemas'];

export type MemoryFact = Schemas['MemoryFactRead'];
export type FactCategory = Schemas['FactCategory'];
