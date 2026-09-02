# Inbox Authentication

The inbox is the only Courier channel that runs client-side, so it is the only one that needs a per-user credential. Generate it server-side; never ship an API key to a browser.

### Common Mistakes

- Minting the JWT in client code. That requires the API key in the browser, which grants full workspace access to anyone who opens devtools.
- Omitting a scope. All four are needed: `user_id:{id} inbox:read:messages inbox:write:events read:preferences`. A partial set returns `401` from the SDK, not a clear scope error.
- Minting a token for one user and signing in as another. Sign out on user switch.
- Letting a token expire instead of refreshing. The socket drops and the inbox silently stops updating.
- Treating a v7 **client key** as interchangeable with a JWT. It isn't, and its own format has a trap, see [v7 client keys](#v7-client-keys).

### Authentication

Courier uses three types of credentials in different contexts:

| Credential | Where used | Exposure |
|------------|-----------|----------|
| **API Key** | Server-side SDK, CLI, raw HTTP (`COURIER_API_KEY` env var) | Never expose to client |
| **Client Key** | Deprecated v7 setups only | Safe for client-side, limited scope |
| **JWT** | Inbox, Preferences, Toast components | Generated server-side, passed to client |

The API Key is the same key regardless of which env var you store it in. The SDK and CLI just look for different variable names by convention.

#### v7 client keys

Only relevant when maintaining a v7 integration ([legacy-v7.md](./legacy-v7.md)). A v7 client key is **base64 of `<tenant>/<env>`**, and that env segment must match the environment of the API key behind it. Two failure modes, one of them silent:

| Client key env segment | Result |
|---|---|
| An `env_01k...` id | Rejected outright, `403` |
| `test` against an env-scoped API key | **`200` with an empty node list.** No error at all |

The second is the single biggest v7 trap: auth looks like it succeeded and the inbox is simply empty.

JWT is required for Inbox. Generate tokens server-side using your API key. The SDKs expose the issue-token endpoint directly. Prefer that over raw HTTP.

**TypeScript (`@trycourier/courier`):**

```typescript
import Courier from "@trycourier/courier";
const client = new Courier(); // reads COURIER_API_KEY

const { token } = await client.auth.issueToken({
  scope: "user_id:user-123 inbox:read:messages inbox:write:events read:preferences",
  expires_in: "7 days",
});
```

**Python (`trycourier`):**

```python
from courier import Courier
client = Courier()  # reads COURIER_API_KEY

resp = client.auth.issue_token(
    scope="user_id:user-123 inbox:read:messages inbox:write:events read:preferences",
    expires_in="7 days",
)
token = resp.token
```

**Raw HTTP** (for languages without a Courier SDK):

```bash
curl -X POST https://api.courier.com/auth/issue-token \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope":"user_id:user-123 inbox:read:messages inbox:write:events read:preferences","expires_in":"7 days"}'
```

### JWT Refresh Strategy

JWTs expire based on `expires_in`. Build a refresh mechanism to avoid broken inbox connections:

```typescript
import Courier from "@trycourier/courier";
const courier = new Courier();

app.get("/api/courier-token", authenticate, async (req, res) => {
  const { token } = await courier.auth.issueToken({
    scope: `user_id:${req.user.id} inbox:read:messages inbox:write:events read:preferences`,
    expires_in: "7 days",
  });
  res.json({ token });
});
```

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
