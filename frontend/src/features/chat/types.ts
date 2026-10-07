import type { components } from '@/lib/api/schema';

// Domain names for the generated API types. Never hand-write shapes the backend defines.
type Schemas = components['schemas'];

export type ConversationSummary = Schemas['ConversationSummary'];
export type ConversationDetail = Schemas['ConversationDetail'];
export type ChatMessage = Schemas['MessageRead'];
export type ChatRunRequest = Schemas['ChatRunRequest'];
export type ChatEvent = Schemas['ChatEvent'];
export type ModelChoice = Schemas['ModelChoice'];
export type ReasoningLevel = Schemas['ReasoningLevel'];
export type Usage = Schemas['Usage'];
export type TextPart = Schemas['TextPart'];
export type ToolPart = Schemas['ToolPart'];
export type MessagePart = TextPart | ToolPart;
export type ModelCall = Schemas['ModelCall'];
export type InputSection = Schemas['InputSection'];
export type InputSectionKind = InputSection['kind'];

// Frontend-only shapes, derived from the generated ones.
export type ChatSettings = Pick<ConversationSummary, 'model' | 'reasoning'>;
