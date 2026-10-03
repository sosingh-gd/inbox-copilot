import { BrandMark } from '../../atoms/BrandMark';
import type { LoadingScreenProps } from './LoadingScreen.types';

export function LoadingScreen({ label = 'Inbox Copilot' }: LoadingScreenProps) {
  return (
    <main aria-busy="true" className="grid min-h-screen place-items-center bg-slate-50">
      <div className="flex flex-col items-center gap-3">
        <BrandMark pulse />
        <p className="text-sm font-medium text-ink-soft">{label}</p>
      </div>
    </main>
  );
}
