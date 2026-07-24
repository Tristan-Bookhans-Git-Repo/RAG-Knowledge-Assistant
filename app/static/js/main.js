// Tokens live only cookies set by the server

// Wrap fetch() for calls that require an authenticated session. If the session
// cookie is missing or expired, the server responds 401 and this redirects to
// /login instead of leaving the caller to silently fail or show a confusing error.

// Do NOT use this for the login/register form submissions in auth.js.
async function authFetch(url, options) {
    const response = await fetch(url, options);
    if (response.status === 401) {
        window.location.href = "/login";
    }
    return response;
}
