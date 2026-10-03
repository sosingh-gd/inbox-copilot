import { api, unwrap } from '@/lib/http';

export const sessionApi = {
  me: (signal?: AbortSignal) => unwrap(api.GET('/api/v1/auth/me', { signal })),
  loginWithGoogle: (code: string) => unwrap(api.POST('/api/v1/auth/google', { body: { code } })),
  logout: () => unwrap(api.POST('/api/v1/auth/logout')),
};
