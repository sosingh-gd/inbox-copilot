import { LogOut } from 'lucide-react';
import { Button } from '@/components';
import { errorMessage } from '@/lib/http';
import { useCurrentUserQuery, useLogoutMutation } from '../../api/session.queries';

export function UserMenu() {
  const { data: user } = useCurrentUserQuery();
  const logout = useLogoutMutation();

  return (
    <>
      <div className="hidden text-right sm:block">
        <p className="max-w-52 truncate text-sm font-medium text-ink">{user?.email}</p>
        {logout.isError && (
          <p className="text-xs text-danger" role="alert">
            {errorMessage(logout.error, 'Could not sign out. Please try again.')}
          </p>
        )}
      </div>
      <Button
        loading={logout.isPending}
        onClick={() => logout.mutate()}
        startIcon={<LogOut className="h-4 w-4" />}
        variant="secondary"
      >
        <span className="hidden sm:inline">{logout.isPending ? 'Signing out' : 'Log out'}</span>
      </Button>
    </>
  );
}
