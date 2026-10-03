import { SplitHeroTemplate } from '@/components';
import { GoogleSignInCard } from '@/features/session';
import { LoginHero } from './LoginHero';

export function LoginPage() {
  return <SplitHeroTemplate hero={<LoginHero />} panel={<GoogleSignInCard />} />;
}
