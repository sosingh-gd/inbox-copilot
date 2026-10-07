import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, unwrap } from '@/lib/http';
import type { MemoryFact } from '../types';

export const memoryKeys = {
  facts: ['memory', 'facts'] as const,
};

export const memoryApi = {
  listFacts: (signal?: AbortSignal) => unwrap(api.GET('/api/v1/memory/facts', { signal })),

  deleteFact: (factId: number) =>
    unwrap(api.DELETE('/api/v1/memory/facts/{fact_id}', { params: { path: { fact_id: factId } } })),
};

/** Everything remembered about the user, most recently changed first. */
export function useMemoryFactsQuery() {
  return useQuery({
    queryKey: memoryKeys.facts,
    queryFn: ({ signal }) => memoryApi.listFacts(signal),
  });
}

export function useDeleteFactMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: memoryApi.deleteFact,
    onSuccess: (_, factId) => {
      queryClient.setQueryData<MemoryFact[]>(memoryKeys.facts, (facts) =>
        facts?.filter((fact) => fact.id !== factId),
      );
    },
  });
}
