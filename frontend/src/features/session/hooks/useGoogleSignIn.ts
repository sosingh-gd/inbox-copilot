import { useGoogleLogin } from '@react-oauth/google';
import { useState } from 'react';
import { GOOGLE_SCOPES } from '@/config/google';
import { errorMessage } from '@/lib/http';
import { useGoogleLoginMutation } from '../api/session.queries';

/**
 * Opens Google's consent popup (authorization-code flow) and exchanges the one-time code
 * with the backend, which sets the session cookie. Google tokens never reach the browser.
 */
export function useGoogleSignIn() {
  const login = useGoogleLoginMutation();
  const [popupError, setPopupError] = useState<string | null>(null);

  const openPopup = useGoogleLogin({
    flow: 'auth-code',
    scope: GOOGLE_SCOPES,
    overrideScope: true,
    onSuccess: ({ code }) => login.mutate(code),
    onError: () => setPopupError('Google sign-in was unsuccessful.'),
    onNonOAuthError: () => setPopupError('Google sign-in was cancelled.'),
  });

  const loginError = login.error
    ? errorMessage(login.error, 'Could not connect your Google account. Please try again.')
    : null;

  return {
    signIn: () => {
      setPopupError(null);
      login.reset();
      openPopup();
    },
    isPending: login.isPending,
    error: popupError ?? loginError,
  };
}
