import { Navigate, Outlet, useLocation } from 'react-router';
import { LoadingScreen } from '@/components';
import { paths } from '@/config/routes';
import { useCurrentUserQuery } from '@/features/session';

/** Guest-only routes (login): signed-in users go back where they came from. */
export function RedirectIfSignedIn() {
  const { data: user, isPending } = useCurrentUserQuery();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  if (isPending) return <LoadingScreen />;
  if (user) return <Navigate replace to={from ?? paths.chats} />;
  return <Outlet />;
}
