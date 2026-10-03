import { z } from 'zod';

// Only VITE_* variables reach the bundle, and they are public. Never put secrets here.
const schema = z.object({
  VITE_GOOGLE_CLIENT_ID: z.string().min(1, 'VITE_GOOGLE_CLIENT_ID is not set (see .env.example)'),
  VITE_API_BASE_URL: z.string().default(''), // '' = same origin (Vite proxy / reverse proxy)
});

const parsed = schema.parse(import.meta.env);

export const env = {
  googleClientId: parsed.VITE_GOOGLE_CLIENT_ID,
  apiBaseUrl: parsed.VITE_API_BASE_URL.replace(/\/$/, ''),
} as const;
