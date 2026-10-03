import { isRouteErrorResponse, useRouteError } from 'react-router';
import { Button, StatusText } from '@/components';

export function RouteError() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : 'Something went wrong while showing this page.';

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-4">
      <div className="flex flex-col items-center gap-4">
        <StatusText align="center" tone="error">
          {message}
        </StatusText>
        <Button onClick={() => window.location.assign('/')} variant="secondary">
          Back to Inbox Copilot
        </Button>
      </div>
    </main>
  );
}
