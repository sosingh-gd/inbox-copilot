import { useNavigate } from 'react-router';
import { AppHeader, AppShellTemplate } from '@/components';
import { paths } from '@/config/routes';
import { MemoryFactList } from '@/features/memory';
import { UserMenu } from '@/features/session';

export function MemoryPage() {
  const navigate = useNavigate();

  return (
    <AppShellTemplate header={<AppHeader actions={<UserMenu />} />}>
      <MemoryFactList onOpenConversation={(id) => navigate(paths.chat(id))} />
    </AppShellTemplate>
  );
}
