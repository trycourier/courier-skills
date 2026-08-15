# Inbox Authentication

The inbox is the only Courier channel that runs client-side, so it is the only one that needs a per-user credential. Generate it server-side; never ship an API key to a browser.

### Authentication

Courier uses three types of credentials in different contexts:

| Credential | Where used | Exposure |
|------------|-----------|----------|
| **API Key** | Server-side SDK, CLI, raw HTTP (`COURIER_API_KEY` env var) | Never expose to client |
| **Client Key** | Deprecated v7 setups only | Safe for client-side, limited scope |
| **JWT** | Inbox, Preferences, Toast components | Generated server-side, passed to client |

The API Key is the same key regardless of which env var you store it in. The SDK and CLI just look for different variable names by convention.

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
