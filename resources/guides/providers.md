# Providers

Configure provider integrations (SendGrid, Twilio, APNS, Slack, etc.) over the `/providers` API. A "provider" here is an instance of a Courier integration in your workspace — i.e. the thing that holds the API key, `from_address`, `messaging_service_sid`, and so on, that Courier uses when delivering a message through that channel.

## Quick Reference

### Rules
- The `provider` field on create must be a **catalog key** (e.g. `"sendgrid"`, `"twilio"`, `"apn"`, `"firebase-fcm"`, `"slack"`). Fetch `/providers/catalog` for the canonical list — do not guess
- `settings` keys are **snake_case on the wire** (e.g. `api_key`, `from_address`, `ip_pool_name`). Each provider's required `settings` schema comes from `/providers/catalog`
- `settings` holds **secrets**. Read them from environment variables; never hardcode in committed code
- `PUT /providers/{id}` is a **full replacement** — always read the current settings, merge, and write back, or you will drop fields
- Provider IDs are opaque workspace-scoped values returned on create (distinct from the catalog `provider` key)
- `title` defaults to `"Default Configuration"` when omitted. For multiple configs of the same provider (e.g. two SendGrid sub-accounts), set a unique `title` and `alias`
- Routing strategies reference providers by their **catalog key** (e.g. `"sendgrid"`) in `channels.{channel}.providers`. If you need multiple configs for the same provider key (two SendGrid sub-accounts, etc.), set distinct `title`/`alias` values and disambiguate in the dashboard — the docs don't yet spec an API-only way to target a specific configuration from a routing strategy

### API vs Dashboard
Prefer the API for:
- Infrastructure-as-code / Terraform-style workspace provisioning
- Multi-workspace rollouts (dev → staging → prod with the same scripted setup)
- AI-agent workflows where the agent already has env-var access to provider credentials
- Programmatic rotation of `api_key`/`auth_token` values

Prefer the dashboard for:
- Day-to-day human credential management (encrypted at rest, team-audited, OAuth flows where available)
- First-time setup of a provider you haven't configured before — the dashboard surfaces required fields interactively
- Providers that use OAuth-based setup (Slack, Gmail, MS Teams, Discord) — these generally still require dashboard-initiated auth

### Common Mistakes
- Guessing `settings` keys instead of reading them from `/providers/catalog` — hallucinated keys are silently ignored and the provider will fail at send time
- Using `provider` values from documentation prose that don't match the catalog (e.g. `"aws_ses"` vs the real `"aws-ses"`, or `"fcm"` vs `"firebase-fcm"`)
- Using `PUT` with only the fields you want to change — it's a full replacement, so any omitted `settings` are wiped
- Committing an `api_key` directly in a `providers.create` call instead of reading `process.env.SENDGRID_API_KEY`
- Creating a provider config via API for a catalog entry that requires OAuth — those need to be initiated from the dashboard

### SDK shape

| Operation | Node | Python |
|-----------|------|--------|
| Create | `client.providers.create({ provider, settings?, title?, alias? })` | `client.providers.create(provider=..., settings=..., ...)` |
| List | `client.providers.list({ cursor? })` | `client.providers.list(cursor=...)` |
| Retrieve | `client.providers.retrieve(id)` | `client.providers.retrieve(id)` |
| Replace | `client.providers.replace(id, { provider, settings, ... })` | `client.providers.replace(id, provider=..., settings=..., ...)` |
| Archive | `client.providers.archive(id)` | `client.providers.archive(id)` |
| Catalog list | `client.providers.catalog.list({ keys?, name?, channel? })` | `client.providers.catalog.list(keys=..., name=..., channel=...)` |

> Providers endpoints are **not yet listed in `https://www.courier.com/docs/llms.txt`**. Fetch these URLs directly when you need the full OpenAPI spec:
> - `https://www.courier.com/docs/api-reference/providers/create-a-provider`
> - `https://www.courier.com/docs/api-reference/providers/list-available-provider-types`
> - `https://www.courier.com/docs/api-reference/providers/list-providers`

---

## Discover Required Settings (`/providers/catalog`)

Before creating a provider config, call the catalog to get the exact `settings` schema. Each field descriptor has `type` and `required`; `enum` types also have `values`.

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

const catalog = await client.providers.catalog.list({ keys: "sendgrid" });

for (const entry of catalog.results) {
  console.log(entry.provider, entry.channel, entry.settings);
  // entry.settings → { api_key: { type: "string", required: true }, ... }
}
```

**Python:**
```python
from courier import Courier

client = Courier()

catalog = client.providers.catalog.list(keys="sendgrid")

for entry in catalog.results:
    print(entry.provider, entry.channel, entry.settings)
```

**curl:**
```bash
# Single provider
curl -s "https://api.courier.com/providers/catalog?keys=sendgrid" \
  -H "Authorization: Bearer $COURIER_API_KEY"

# All email providers
curl -s "https://api.courier.com/providers/catalog?channel=email" \
  -H "Authorization: Bearer $COURIER_API_KEY"

# Substring search on display name
curl -s "https://api.courier.com/providers/catalog?name=grid" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Use the returned `settings` map to build your `providers.create` payload. Any field with `required: true` must be present.

---

## Create a Provider

### SendGrid (worked example)

After consulting the catalog you know SendGrid needs `api_key` (required) and optionally `from_address`, `ip_pool_name`, etc.

**TypeScript:**
```typescript
const provider = await client.providers.create({
  provider: "sendgrid",
  title: "SendGrid — Production",
  alias: "sendgrid-prod",
  settings: {
    api_key: process.env.SENDGRID_API_KEY!,
    from_address: "notifications@acme.co"
  }
});

const providerId = provider.id;
```

**Python:**
```python
import os

provider = client.providers.create(
    provider="sendgrid",
    title="SendGrid — Production",
    alias="sendgrid-prod",
    settings={
        "api_key": os.environ["SENDGRID_API_KEY"],
        "from_address": "notifications@acme.co",
    },
)

provider_id = provider.id
```

**curl:**
```bash
curl -X POST "https://api.courier.com/providers" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"provider\": \"sendgrid\",
    \"title\": \"SendGrid — Production\",
    \"alias\": \"sendgrid-prod\",
    \"settings\": {
      \"api_key\": \"$SENDGRID_API_KEY\",
      \"from_address\": \"notifications@acme.co\"
    }
  }"
```

### Twilio

```typescript
await client.providers.create({
  provider: "twilio",
  settings: {
    account_sid: process.env.TWILIO_ACCOUNT_SID!,
    auth_token: process.env.TWILIO_AUTH_TOKEN!,
    messaging_service_sid: "MG..." // or `from` for a single number
  }
});
```

After creating the provider, reference it by catalog key in a routing strategy — see [routing-strategies.md](./routing-strategies.md):

```typescript
await client.routingStrategies.create({
  name: "Transactional",
  routing: { method: "single", channels: ["email", "sms"] },
  channels: {
    email: { providers: ["sendgrid"] },
    sms: { providers: ["twilio"] }
  }
});
```

---

## List, Retrieve, Replace, Archive

### List

**TypeScript:**
```typescript
const { results, paging } = await client.providers.list();
for (const p of results) console.log(p.id, p.provider, p.title, p.alias);
```

**Python:**
```python
response = client.providers.list()
for p in response.results:
    print(p.id, p.provider, p.title, p.alias)
```

**curl:**
```bash
curl -s "https://api.courier.com/providers" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Retrieve

**TypeScript:**
```typescript
const provider = await client.providers.retrieve("provider_01abc123");
```

**Python:**
```python
provider = client.providers.retrieve("provider_01abc123")
```

### Replace (rotate an API key safely)

Replace is full-document — read, modify, write back.

**TypeScript:**
```typescript
const current = await client.providers.retrieve("provider_01abc123");

await client.providers.replace("provider_01abc123", {
  provider: current.provider,
  title: current.title,
  alias: current.alias,
  settings: {
    ...current.settings,
    api_key: process.env.SENDGRID_API_KEY_NEW! // rotated key
  }
});
```

**Python:**
```python
current = client.providers.retrieve("provider_01abc123")

client.providers.replace(
    "provider_01abc123",
    provider=current.provider,
    title=current.title,
    alias=current.alias,
    settings={**current.settings, "api_key": os.environ["SENDGRID_API_KEY_NEW"]},
)
```

### Archive

**TypeScript:**
```typescript
await client.providers.archive("provider_01abc123");
```

**Python:**
```python
client.providers.archive("provider_01abc123")
```

**curl:**
```bash
curl -X DELETE "https://api.courier.com/providers/provider_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Unlink the provider from any routing strategies (remove its key from each `channels.{channel}.providers` array) before archiving to avoid silent send failures.

---

## Per-send provider overrides (recap)

You don't need to create or replace a provider config to tweak a single send. Pass `providers.{key}.override` on the Send API instead:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_...",
    providers: {
      sendgrid: { override: { ip_pool_name: "marketing" } },
      twilio: { override: { messaging_service_sid: "MG..." } }
    }
  }
});
```

See [multi-channel.md](./multi-channel.md#provider-failover) for failover semantics and [routing-strategies.md](./routing-strategies.md) for workspace-level provider priority.

---

## Related

- [Routing Strategies](./routing-strategies.md) — reference providers in `channels.{channel}.providers`
- [Multi-Channel](./multi-channel.md) — failover semantics, per-send `providers.{key}.override`
- [Email](../channels/email.md), [SMS](../channels/sms.md), [Push](../channels/push.md) — channel-specific deliverability considerations
- [Create a provider](https://www.courier.com/docs/api-reference/providers/create-a-provider) — official endpoint reference
- [List available provider types](https://www.courier.com/docs/api-reference/providers/list-available-provider-types) — `/providers/catalog` reference
- [Integrations Overview](https://www.courier.com/docs/external-integrations/integrations-overview) — human-facing integration docs

<!-- Target line budget: <= 500 lines. -->
