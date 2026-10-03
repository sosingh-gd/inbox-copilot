import { createBrowserRouter, Navigate } from 'react-router';
import { paths } from '@/config/routes';
import { RedirectIfSignedIn } from './RedirectIfSignedIn';
import { RequireAuth } from './RequireAuth';
import { RouteError } from './RouteError';

// Pages are lazy-loaded so each route only downloads its own code.
export const router = createBrowserRouter([
  {
    errorElement: <RouteError />,
    children: [
      { path: paths.home, element: <Navigate replace to={paths.chats} /> },
      {
        element: <RedirectIfSignedIn />,
        children: [
          {
            path: paths.login,
            lazy: () => import('@/pages/LoginPage').then((m) => ({ Component: m.LoginPage })),
          },
        ],
      },
      {
        element: <RequireAuth />,
        children: [
          {
            // One route for "new" and existing conversations, so the page stays mounted
            // (and keeps streaming) when a new conversation gets its id.
            path: `${paths.chats}/:conversationId?`,
            lazy: () => import('@/pages/ChatPage').then((m) => ({ Component: m.ChatPage })),
          },
        ],
      },
      { path: '*', element: <Navigate replace to={paths.home} /> },
    ],
  },
]);
