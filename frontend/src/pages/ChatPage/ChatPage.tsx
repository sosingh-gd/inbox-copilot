import { useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { AppHeader, AppShellTemplate } from '@/components';
import { paths } from '@/config/routes';
import { ChatPanel, ConversationList } from '@/features/chat';
import { UserMenu, useCurrentUserQuery } from '@/features/session';

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const { data: user } = useCurrentUserQuery();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const openConversation = (id?: string) => {
    navigate(id ? paths.chat(id) : paths.chats);
    setIsSidebarOpen(false);
  };

  return (
    <AppShellTemplate
      header={
        <AppHeader
          actions={<UserMenu />}
          menuLabel="Open conversations"
          onMenuClick={() => setIsSidebarOpen(true)}
        />
      }
      isSidebarOpen={isSidebarOpen}
      onSidebarClose={() => setIsSidebarOpen(false)}
      sidebar={
        <ConversationList
          activeConversationId={conversationId}
          onNewConversation={() => openConversation()}
          onSelect={openConversation}
        />
      }
      sidebarTitle="Conversations"
    >
      {/* The key gives each conversation a fresh panel, so no state carries over. */}
      <ChatPanel
        conversationId={conversationId}
        key={conversationId ?? 'new'}
        onConversationCreated={(id) => navigate(paths.chat(id), { replace: true })}
        userInitial={user?.email.charAt(0).toUpperCase() ?? '?'}
      />
    </AppShellTemplate>
  );
}
