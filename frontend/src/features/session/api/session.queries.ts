import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { isApiError } from '@/lib/http';
import type { CurrentUser } from '../types';
import { sessionApi } from './session.api';
import { sessionKeys } from './session.keys';

/** The signed-in user, or `null` when signed out. */
export function useCurrentUserQuery() {
  return useQuery({
    queryKey: sessionKeys.me,
    queryFn: async ({ signal }): Promise<CurrentUser | null> => {
      try {
        return await sessionApi.me(signal);
      } catch (err) {
        if (isApiError(err) && err.status === 401) return null;
        throw err;
      }
    },
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function useGoogleLoginMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: sessionApi.loginWithGoogle,
    onSuccess: (user) => queryClient.setQueryData(sessionKeys.me, user),
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: sessionApi.logout,
    onSuccess: () => {
      // Drop every cached query so the next user never sees this user's data.
      queryClient.clear();
      queryClient.setQueryData(sessionKeys.me, null);
    },
  });
}
