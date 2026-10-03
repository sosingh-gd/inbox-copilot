import { Button, StatusText } from '@/components';
import { useGoogleSignIn } from '../../hooks/useGoogleSignIn';
import { GoogleIcon } from '../GoogleIcon';

export function GoogleSignInCard() {
  const { signIn, isPending, error } = useGoogleSignIn();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm font-semibold uppercase text-brand">Welcome</p>
        <h2 className="mt-3 text-3xl font-semibold text-ink">Sign in to continue</h2>
        <p className="mt-3 leading-7 text-ink-soft">
          Use the Google account you want Inbox Copilot to organize.
        </p>
      </div>

      <Button
        fullWidth
        loading={isPending}
        onClick={signIn}
        size="lg"
        startIcon={<GoogleIcon />}
        variant="secondary"
      >
        {isPending ? 'Connecting…' : 'Continue with Google'}
      </Button>

      {error && (
        <StatusText align="center" tone="error">
          {error}
        </StatusText>
      )}

      <div className="flex items-center gap-4 text-sm text-ink-muted">
        <span className="h-px flex-1 bg-slate-200" />
        OAuth 2.0
        <span className="h-px flex-1 bg-slate-200" />
      </div>

      <p className="rounded-lg bg-surface-soft p-4 text-sm leading-6 text-ink-soft">
        Inbox Copilot asks Google for read-only access to your mail and calendar. It never sends
        email or changes events without your confirmation.
      </p>
    </div>
  );
}
