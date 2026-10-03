import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';
import { isApiError } from './http';

/** Query key of the signed-in user. `null` means signed out. */
export const SESSION_KEY = ['session', 'me'] as const;

export function createQueryClient(): QueryClient {
  // One place reacts to expired sessions (and revoked Google access): the route guard sees
  // no user and redirects to the login page.
  const onError = (err: unknown) => {
    if (isApiError(err) && err.status === 401) client.setQueryData(SESSION_KEY, null);
  };

  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        // Never retry 4xx; retry 5xx / network errors up to twice.
        retry: (count, err) => !(isApiError(err) && err.status < 500) && count < 2,
      },
    },
  });
  return client;
}

export const queryClient = createQueryClient();
