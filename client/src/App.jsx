const GoogleIcon = () => (
  <svg
    aria-hidden="true"
    className="h-5 w-5 shrink-0"
    viewBox="0 0 24 24"
  >
    <path
      fill="#4285F4"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="#34A853"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="#FBBC05"
      d="M5.84 14.1c-.22-.66-.35-1.36-.35-2.1s.13-1.44.35-2.1V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l3.66-2.84z"
    />
    <path
      fill="#EA4335"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06L5.84 9.9C6.71 7.3 9.14 5.38 12 5.38z"
    />
  </svg>
);

function App() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,var(--color-skywash),transparent_32rem),linear-gradient(135deg,var(--color-page),var(--color-page-muted))] px-5 py-8 text-ink sm:px-8">
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="max-w-2xl">
          <div className="mb-8 inline-flex items-center gap-3 rounded-full border border-white/70 bg-white/70 px-4 py-2 text-sm font-medium text-ink-soft shadow-sm backdrop-blur">
            <span className="h-2.5 w-2.5 rounded-full bg-brand" />
            Inbox Copilot
          </div>

          <h1 className="max-w-2xl text-5xl font-semibold leading-[1.02] tracking-normal text-ink sm:text-6xl">
            A quieter inbox starts with one secure sign-in.
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-8 text-ink-soft">
            Connect your Google account to help Inbox Copilot organize messages,
            surface priorities, and keep the daily email sweep focused.
          </p>

          <div className="mt-10 grid max-w-xl gap-4 sm:grid-cols-3">
            {["Private by default", "Smart triage", "Fast setup"].map((item) => (
              <div
                className="rounded-lg border border-white/80 bg-white/65 px-4 py-3 text-sm font-medium text-ink-soft shadow-sm backdrop-blur"
                key={item}
              >
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="mx-auto w-full max-w-md rounded-[1.75rem] border border-white/80 bg-white/85 p-6 shadow-2xl shadow-ink/10 backdrop-blur md:p-8">
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">
              Welcome
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-normal text-ink">
              Sign in to continue
            </h2>
            <p className="mt-3 leading-7 text-ink-soft">
              Use the Google account you want Inbox Copilot to organize.
            </p>
          </div>

          <button
            className="group flex h-14 w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white px-5 text-base font-semibold text-ink shadow-sm transition hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-lg hover:shadow-brand/10 focus:outline-none focus:ring-4 focus:ring-brand/20"
            type="button"
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="my-7 flex items-center gap-4 text-sm text-ink-muted">
            <span className="h-px flex-1 bg-slate-200" />
            OAuth 2.0
            <span className="h-px flex-1 bg-slate-200" />
          </div>

          <div className="rounded-lg bg-surface-soft p-4 text-sm leading-6 text-ink-soft">
            We will ask Google only for the permissions needed to personalize
            your inbox workflow.
          </div>

          <p className="mt-6 text-center text-xs leading-6 text-ink-muted">
            By continuing, you agree to connect Inbox Copilot with your selected
            Google account.
          </p>
        </div>
      </section>
    </main>
  );
}

export default App;
