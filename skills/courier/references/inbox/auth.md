# Inbox Authentication

The inbox is the only Courier channel that runs client-side, so it is the only one that needs a per-user credential.

**Contents:** [Quick Reference](#quick-reference) · [Authentication](#authentication) · [Minting a JWT](#minting-a-jwt) · [JWT Refresh Strategy](#jwt-refresh-strategy)

## Quick Reference

### Rules

- **Mint the JWT server-side.** Minting it in client code needs the API key in the browser, which grants full workspace access to anyone who opens devtools.
- **Scopes:** `user_id:{id}` ties the token to one user. Reading needs `inbox:read:messages`; marking read, opened, or archived needs `inbox:write:events`. A token missing either still signs in and the feed loads empty with no error, not a `401`. Add `read:preferences write:preferences` only if you mount preferences; without them the preference center is empty.
- **Sign out on user switch.** Never sign in with a token minted for another user.
- **Refresh before expiry.** An expired token drops the socket and the inbox silently stops updating.
- A v7 **client key** is not a JWT, and its format has its own trap, see [legacy-v7.md](./legacy-v7.md#common-mistakes).

### Authentication

Three credentials: the **API key** (server-side SDK, CLI, and raw HTTP; never in a client), the **JWT** (minted server-side, used by the inbox, preferences, and toast components), and the legacy v7 **client key**, covered only in [legacy-v7.md](./legacy-v7.md).

### Minting a JWT

Mint it server-side with the SDK's issue-token call, from an endpoint your signed-in client fetches:

```typescript
import Courier from "@trycourier/courier";
const courier = new Courier();

app.get("/api/courier-token", authenticate, async (req, res) => {
  const { token } = await courier.auth.issueToken({
    scope: `user_id:${req.user.id} inbox:read:messages inbox:write:events read:preferences write:preferences`,
    expires_in: "7 days",
  });
  res.json({ token });
});
```

Python: `client.auth.issue_token(scope=..., expires_in=...)`, token in `.token`. Without an SDK: `POST https://api.courier.com/auth/issue-token` with the same `scope` and `expires_in` JSON body.

### JWT Refresh Strategy

JWTs expire based on `expires_in`. Refresh on the client before expiry:

```tsx
// Client-side: refresh before expiry
function useCourierToken(userId: string) {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const fetchToken = () =>
      fetch("/api/courier-token")
        .then((r) => r.json())
        .then((d) => setToken(d.token));

    fetchToken();
    const interval = setInterval(fetchToken, 6 * 24 * 60 * 60 * 1000); // refresh 1 day before 7-day expiry
    return () => clearInterval(interval);
  }, [userId]);

  return token;
}
```
