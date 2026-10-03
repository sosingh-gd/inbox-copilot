import type { ReactNode } from 'react';

export interface SplitHeroTemplateProps {
  /** Left column: marketing copy. */
  hero: ReactNode;
  /** Right column: usually a card with the primary action. */
  panel: ReactNode;
}
