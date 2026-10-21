# Providers

Configure provider integrations (SendGrid, Twilio, APNS, Slack, etc.) over the `/providers` API. A "provider" here is an instance of a Courier integration in your workspace, i.e. the thing that holds the API key, `from_address`, `messaging_service_sid`, and so on, that Courier uses when delivering a message through that channel.

## Quick Reference

### Rules
- The `provider` field on create must be a **catalog key** (e.g. `"sendgrid"`, `"twilio"`, `"apn"`, `"firebase-fcm"`, `"slack"`). Fetch `/providers/catalog` for the canonical list. Do not guess
- `settings` keys are **snake_case on the wire** (e.g. `api_key`, `from_address`, `ip_pool_name`). Each provider's required `settings` schema comes from `/providers/catalog`
- `settings` holds **secrets**. Read them from environment variables; never hardcode in committed code
- To change part of a config (one setting, the `title`, or the `alias`), use **`PATCH /providers/{id}`** (`client.providers.patch`). Fields you leave out keep their stored values, so there's nothing to read back first. See [Update part of a config](#update-part-of-a-config-patch)
- `PUT /providers/{id}` (`client.providers.update`) is a **full replacement**. Use it only when you intend to replace the whole config
- To cap how fast Courier sends through a provider config, set `settings.rate_limit` with `PATCH`. See [Send rate limits](#send-rate-limits)
- Provider IDs are opaque workspace-scoped values returned on create (distinct from the catalog `provider` key)
- `title` defaults to `"Default Configuration"` when omitted. For multiple configs of the same provider (e.g. two SendGrid sub-accounts), set a unique `title` and `alias`
- Routing strategies reference providers by their **catalog key** (e.g. `"sendgrid"`) in `channels.{channel}.providers`. If you need multiple configs for the same provider key (two SendGrid sub-accounts, etc.), set distinct `title`/`alias` values and disambiguate in the dashboard, the docs don't yet spec an API-only way to target a specific configuration from a routing strategy

### API vs Dashboard
Prefer the API for:
- Infrastructure-as-code / Terraform-style workspace provisioning
- Multi-workspace rollouts (dev → staging → prod with the same scripted setup)
- AI-agent workflows where the agent already has env-var access to provider credentials
- Programmatic rotation of `api_key`/`auth_token` values

Prefer the dashboard for:
- Day-to-day human credential management (encrypted at rest, team-audited, OAuth flows where available)
- First-time setup of a provider you haven't configured before, the dashboard surfaces required fields interactively
- Providers that use OAuth-based setup (Slack, Gmail, MS Teams, Discord), these generally still require dashboard-initiated auth

### Common Mistakes
- Guessing `settings` keys instead of reading them from `/providers/catalog`. A missing or misspelled required key returns 400 on create, and a misspelled optional key doesn't set the option you meant
- Using `provider` values from documentation prose that don't match the catalog (e.g. `"aws_ses"` vs the real `"aws-ses"`, or `"fcm"` vs `"firebase-fcm"`)
- Using `PUT` to change one setting. It's a full replacement, so any omitted `settings` are wiped, including `rate_limit`. Use `PATCH` instead
- Committing an `api_key` directly in a `providers.create` call instead of reading `process.env.SENDGRID_API_KEY`
- Creating a provider config via API for a catalog entry that requires OAuth, those need to be initiated from the dashboard

### SDK shape

| Operation | Node | Python |
|-----------|------|--------|
| Create | `client.providers.create({ provider, settings?, title?, alias? })` | `client.providers.create(provider=..., settings=..., ...)` |
| List | `client.providers.list({ cursor? })` | `client.providers.list(cursor=...)` |
| Retrieve | `client.providers.retrieve(id)` | `client.providers.retrieve(id)` |
| Update part (PATCH) | `client.providers.patch(id, { settings?, title?, alias? })` | `client.providers.patch(id=..., settings=..., ...)` |
| Replace (full PUT) | `client.providers.update(id, { provider, settings, ... })` | `client.providers.update(id, provider=..., settings=..., ...)` |
| Delete | `client.providers.delete(id)` | `client.providers.delete(id)` |
| Catalog list | `client.providers.catalog.list({ keys?, name?, channel? })` | `client.providers.catalog.list(keys=..., name=..., channel=...)` |

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

After creating the provider, reference it by catalog key in a routing strategy. See [routing-strategies.md](./routing-strategies.md):

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

## List, Retrieve, Update, Replace, Delete

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

### Update part of a config (PATCH)

`PATCH /providers/{id}` merges the body into the stored config using JSON Merge Patch (RFC 7396):

- Fields you leave out keep their stored values
- A setting sent as `null` is removed
- Nested objects merge, and arrays replace the stored value
- `alias: null` clears the alias
- The body must include at least one of `title`, `alias`, or `settings`. An empty body returns a `400`
- `provider` is optional. If you send it, it must match the stored provider, otherwise the request returns a `400`
- A missing or archived id returns a `404`

Rotate an API key and leave everything else as it is:

**TypeScript:**
```typescript
await client.providers.patch("provider_01abc123", {
  settings: { api_key: process.env.SENDGRID_API_KEY_NEW! }
});
```

**Python:**
```python
client.providers.patch(
    id="provider_01abc123",
    settings={"api_key": os.environ["SENDGRID_API_KEY_NEW"]},
)
```

**curl:**
```bash
curl -X PATCH "https://api.courier.com/providers/provider_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"settings\": {\"api_key\": \"$SENDGRID_API_KEY_NEW\"}}"
```

Rename a config and clear its alias:

```typescript
await client.providers.patch("provider_01abc123", { title: "SendGrid Marketing", alias: null });
```

### Replace the whole config (PUT)

`PUT /providers/{id}` replaces the config in full. `provider` is required, and every field you omit is cleared, including `alias` and any `settings` key such as `rate_limit`. Use it when you intend to define the complete config, for example from a provisioning script that owns every field. To change one setting, use [PATCH](#update-part-of-a-config-patch).

**TypeScript:**
```typescript
await client.providers.update("provider_01abc123", {
  provider: "sendgrid",
  title: "SendGrid Production",
  alias: "sendgrid-prod",
  settings: {
    api_key: process.env.SENDGRID_API_KEY!,
    from_address: "notifications@acme.co"
  }
});
```

**Python:**
```python
client.providers.update(
    "provider_01abc123",
    provider="sendgrid",
    title="SendGrid Production",
    alias="sendgrid-prod",
    settings={
        "api_key": os.environ["SENDGRID_API_KEY"],
        "from_address": "notifications@acme.co",
    },
)
```

### Delete

**TypeScript:**
```typescript
await client.providers.delete("provider_01abc123");
```

**Python:**
```python
client.providers.delete("provider_01abc123")
```

**curl:**
```bash
curl -X DELETE "https://api.courier.com/providers/provider_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Delete returns 409 while any routing strategy or template still references the provider. Remove its key from each strategy's `channels.{channel}.providers` array and update those templates first.

---

## Send rate limits

Cap how fast Courier sends through one provider configuration with `settings.rate_limit`:

```json
{ "rate": 10, "period": "second" }
```

- `rate` is a number greater than 0. Fractions are allowed, so `{ "rate": 0.5, "period": "minute" }` is one send every 2 minutes
- `period` is `"second"`, `"minute"`, or `"hour"`
- The interval between sends (`period` divided by `rate`) must be from 1 ms to 12 hours, otherwise the API returns a `400` `InvalidRateLimit`
- The limit is per provider configuration and per environment
- Sends above the rate are queued, not dropped
- Changes apply within 60 seconds
- With no limit set, Courier sends as fast as it can
- The Courier Inbox (`courier`) provider has no rate limit field in the console. Don't suggest setting one there

Set or change it with `PATCH`, so the rest of the config stays as it is:

**TypeScript:**
```typescript
await client.providers.patch("provider_01abc123", {
  settings: { rate_limit: { rate: 10, period: "second" } }
});
```

**Python:**
```python
client.providers.patch(
    id="provider_01abc123",
    settings={"rate_limit": {"rate": 10, "period": "second"}},
)
```

**curl:**
```bash
curl -X PATCH "https://api.courier.com/providers/provider_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "settings": { "rate_limit": { "rate": 10, "period": "second" } } }'
```

Remove it by sending `null`:

**TypeScript:**
```typescript
await client.providers.patch("provider_01abc123", { settings: { rate_limit: null } });
```

**Python:**
```python
client.providers.patch(id="provider_01abc123", settings={"rate_limit": None})
```

**curl:**
```bash
curl -X PATCH "https://api.courier.com/providers/provider_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "settings": { "rate_limit": null } }'
```

---

## Per-send provider overrides (recap)

You don't need to create or replace a provider config to tweak a single send. Pass `providers.{key}.override` on the Send API instead:

```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_...",
    providers: {
      sendgrid: { override: { body: { ip_pool_name: "marketing" } } },
      twilio: { override: { body: { MessagingServiceSid: "MG..." } } }
    }
  }
});
```

`body` merges into the provider's own request, so use that API's field names.

See [multi-channel.md](./multi-channel.md#provider-failover) for failover semantics and [routing-strategies.md](./routing-strategies.md) for workspace-level provider priority.

---

## Related

- [Routing Strategies](./routing-strategies.md), reference providers in `channels.{channel}.providers`
- [Multi-Channel](./multi-channel.md), failover semantics, per-send `providers.{key}.override`
- [Email](../channels/email.md), [SMS](../channels/sms.md), [Push](../channels/push.md), channel-specific deliverability considerations
- [Create a provider](https://www.courier.com/docs/api-reference/providers/create-a-provider), official endpoint reference
- [List available provider types](https://www.courier.com/docs/api-reference/providers/list-available-provider-types), `/providers/catalog` reference
- [Integrations Overview](https://www.courier.com/docs/integrations/overview), human-facing integration docs

<!-- Target line budget: <= 500 lines. -->
