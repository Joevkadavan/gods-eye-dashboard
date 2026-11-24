/**
 * Send an operator-only request with a short-lived, user-entered admin token.
 * The bearer secret is never compiled into the frontend bundle or stored on disk.
 */
const TOKEN_KEY = 'gods-eye-admin-token';

export async function adminFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  let token = window.sessionStorage.getItem(TOKEN_KEY);
  if (!token) {
    token = window.prompt('Enter the GOD’S EYE administrator API token supplied by the deployment operator');
    if (!token) throw new Error('Administrator token is required for this action');
    token = token.trim();
    if (!token) throw new Error('Administrator token is required for this action');
    window.sessionStorage.setItem(TOKEN_KEY, token);
  }

  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    window.sessionStorage.removeItem(TOKEN_KEY);
  }
  return response;
}
