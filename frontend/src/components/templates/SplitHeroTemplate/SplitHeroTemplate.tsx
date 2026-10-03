import type { SplitHeroTemplateProps } from './SplitHeroTemplate.types';

export function SplitHeroTemplate({ hero, panel }: SplitHeroTemplateProps) {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,var(--color-skywash),transparent_32rem),linear-gradient(135deg,var(--color-page),var(--color-page-muted))] px-5 py-8 text-ink sm:px-8">
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="max-w-2xl">{hero}</div>
        <div className="mx-auto w-full max-w-md rounded-lg border border-white/80 bg-white/85 p-6 shadow-2xl shadow-ink/10 backdrop-blur md:p-8">
          {panel}
        </div>
      </section>
    </main>
  );
}
