const HIGHLIGHTS = ['Private by default', 'Smart triage', 'Fast setup'] as const;

export function LoginHero() {
  return (
    <>
      <div className="mb-8 inline-flex items-center gap-3 rounded-full border border-white/70 bg-white/70 px-4 py-2 text-sm font-medium text-ink-soft shadow-sm backdrop-blur">
        <span className="h-2.5 w-2.5 rounded-full bg-brand" />
        Inbox Copilot
      </div>
      <h1 className="max-w-2xl text-5xl font-semibold leading-[1.02] text-ink">
        A quieter inbox starts with one secure sign-in.
      </h1>
      <p className="mt-6 max-w-xl text-lg leading-8 text-ink-soft">
        Connect your Google account to help Inbox Copilot organize messages, surface priorities, and
        keep the daily email sweep focused.
      </p>
      <ul className="mt-10 grid max-w-xl gap-4 sm:grid-cols-3">
        {HIGHLIGHTS.map((item) => (
          <li
            className="rounded-lg border border-white/80 bg-white/65 px-4 py-3 text-sm font-medium text-ink-soft shadow-sm backdrop-blur"
            key={item}
          >
            {item}
          </li>
        ))}
      </ul>
    </>
  );
}
