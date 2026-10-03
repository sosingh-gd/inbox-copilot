import type { components } from '@/lib/api/schema';

// Domain names for the generated API types. Never hand-write shapes the backend defines.
type Schemas = components['schemas'];

export type ConversationSummary = Schemas['ConversationSummary'];
export type ConversationDetail = Schemas['ConversationDetail'];
export type ChatMessage = Schemas['MessageRead'];
export type ChatRunRequest = Schemas['ChatRunRequest'];
export type ChatEvent = Schemas['ChatEvent'];
export type AgentKind = Schemas['AgentKind'];
export type ModelChoice = Schemas['ModelChoice'];
export type ReasoningLevel = Schemas['ReasoningLevel'];

// Frontend-only shapes, derived from the generated ones.
export type ChatSettings = Pick<ConversationSummary, 'agent' | 'model' | 'reasoning'>;

export type DisplayMessage = Pick<ChatMessage, 'id' | 'role' | 'content'>;
