import { Navigate, Outlet, useLocation } from 'react-router';
import { LoadingScreen } from '@/components';
import { paths } from '@/config/routes';
import { useCurrentUserQuery } from '@/features/session';

/** Renders child routes for signed-in users; sends everyone else to the login page. */
export function RequireAuth() {
  const { data: user, isPending, isError } = useCurrentUserQuery();
  const location = useLocation();

  if (isPending) return <LoadingScreen />;
  if (isError)
    return <LoadingScreen label="Could not reach Inbox Copilot. Is the backend running?" />;
  if (!user) return <Navigate replace state={{ from: location.pathname }} to={paths.login} />;
  return <Outlet />;
}
