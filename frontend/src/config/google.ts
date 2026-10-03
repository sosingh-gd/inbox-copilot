// Must match GOOGLE_OAUTH_SCOPES in backend/app/core/config.py.
export const GOOGLE_SCOPES = [
  'openid',
  'profile',
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/calendar.readonly',
].join(' ');
