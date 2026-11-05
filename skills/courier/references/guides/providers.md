# Providers

Configure provider integrations (SendGrid, Twilio, APNS, Slack, etc.) over the `/providers` API. A "provider" here is an instance of a Courier integration in your workspace, i.e. the thing that holds the API key, `from_address`, `messaging_service_sid`, and so on, that Courier uses when delivering a message through that channel.

**Contents:** [Quick Reference](#quick-reference) · [Discover Required Settings (/providers/catalog)](#discover-required-settings-providerscatalog) · [Create a Provider](#create-a-provider) · [List, Retrieve, Update, Replace, Delete](#list-retrieve-update-replace-delete) · [Send rate limits](#send-rate-limits) · [Per-send provider overrides (recap)](#per-send-provider-overrides-recap) · [Related](#related)

## Quick Reference

### Rules
- The `provider` field on create must be a **catalog key** (e.g. `"sendgrid"`, `"twilio"`, `"apn"`, `"firebase-fcm"`, `"slack"`). Fetch `/providers/catalog` for the canonical list. Do not guess
- `settings` keys are **snake_case on the wire** (e.g. `api_key`, `from_address`, `ip_pool_name`). Each provider's required `settings` schema comes from `/providers/catalog`
- `settings` holds **secrets**. Read them from environment variables; never hardcode in committed code
- To change part of a config (one setting, the `title`, or the `alias`), use **`PATCH /providers/{id}`** (`client.providers.patch`). It takes JSON Patch (RFC 6902) operations in `patch`, such as `{ op: "replace", path: "/settings/api_key", value }`, and keeps every field they don't touch. See [Update part of a config](#update-part-of-a-config-patch)
- `PUT /providers/{id}` (`client.providers.update`) is a **full replacement**. Use it only when you intend to replace the whole config
- To cap how fast Courier sends through a provider config, `add` `/settings/rate_limit` with `PATCH`. See [Send rate limits](#send-rate-limits)
- Provider IDs are opaque workspace-scoped values returned on create (distinct from the catalog `provider` key)
- `title` defaults to `"Default Configuration"` when omitted. For multiple configs of the same provider (e.g. two SendGrid sub-accounts), set a unique `title` and `alias`
- In the test environment, a stored `title` gets a `test - ` prefix
- Routing strategies reference providers by their **catalog key** (e.g. `"sendgrid"`) in `channels.{channel}.providers`. There's no documented API way to target one of several configs of the same provider from a strategy; tell them apart by `title`/`alias` in the dashboard

### Common Mistakes
- Guessing `settings` keys instead of reading them from `/providers/catalog`. A misspelled or unknown `settings` key is saved silently and does nothing. Read the catalog and compare the stored config with `GET /providers/{id}`. Only a missing required key is rejected: `400`, with the field named in camelCase (e.g. `authToken`)
- Using `provider` values from documentation prose that don't match the catalog (e.g. `"aws_ses"` vs the real `"aws-ses"`, or `"fcm"` vs `"firebase-fcm"`)
- Using `PUT` to change one setting. It's a full replacement, so any omitted `settings` are wiped, including `rate_limit`. Use `PATCH` instead
- Sending the fields to change as the `PATCH` body (`{ settings: { … } }`). The body is `{ patch: [operations] }`; a plain object returns `400 patch: must be an array of JSON Patch operations`
- Creating a provider config via API for a catalog entry that requires OAuth, those need to be initiated from the dashboard

### SDK shape

| Operation | Node | Python |
|-----------|------|--------|
| Create | `client.providers.create({ provider, settings?, title?, alias? })` | `client.providers.create(provider=..., settings=..., ...)` |
| List | `client.providers.list({ cursor? })` | `client.providers.list(cursor=...)` |
| Retrieve | `client.providers.retrieve(id)` | `client.providers.retrieve(id)` |
| Update part (PATCH) | `client.providers.patch(id, { patch: [{ op, path, value? }] })` | `client.providers.patch(id, patch=[{"op": ..., "path": ..., "value": ...}])` |
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

Filter with `keys` (exact catalog keys), `channel` (e.g. `email`), or `name` (substring of the display name), in the SDK or as query params on `GET /providers/catalog`. Every field with `required: true` must be in your `providers.create` payload.

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

Then reference each provider by its catalog key (`"sendgrid"`, `"twilio"`) in a routing strategy's `channels.{channel}.providers`, see [routing-strategies.md](./routing-strategies.md).

---

## List, Retrieve, Update, Replace, Delete

### List and retrieve

`client.providers.list({ cursor? })` returns `{ results, paging }`, each with `id`, `provider`, `title`, and `alias`. `client.providers.retrieve(id)` returns one config.

### Update part of a config (PATCH)

`PATCH /providers/{id}` applies JSON Patch (RFC 6902) operations, sent as `{ "patch": [...] }`, and keeps every field the operations don't touch:

- Paths address the provider as it's returned: `/title`, `/alias`, `/provider`, and `/settings/<key>` with the snake_case setting keys. Nested paths such as `/settings/rate_limit/rate` work
- `op` is `add`, `remove`, `replace`, `move`, `copy` or `test`. `add` sets a value whether or not it exists
- Operations apply in order. If one fails, for example a `test`, nothing is saved and the request returns a `400`
- An empty `patch` array returns a `400`
- The result can't change `provider`, remove `title`, or add other top-level fields. Each returns a `400`
- Removing `/alias` clears the alias
- A missing or deleted id returns a `404`

Rotate an API key and leave everything else as it is:

**TypeScript:**
```typescript
await client.providers.patch("provider_01abc123", {
  patch: [{ op: "replace", path: "/settings/api_key", value: process.env.SENDGRID_API_KEY_NEW! }],
});
```

Python: `client.providers.patch("provider_01abc123", patch=[{"op": "replace", "path": "/settings/api_key", "value": ...}])`. curl: `PATCH https://api.courier.com/providers/{id}` with the body `{"patch": [...]}`.

To apply a change only if the stored config is what you expect, put a `test` operation first. If it fails, the request returns `400` and nothing changes:

```typescript
await client.providers.patch("provider_01abc123", {
  patch: [
    { op: "test", path: "/settings/from_address", value: "notifications@acme.co" },
    { op: "replace", path: "/settings/from_address", value: "alerts@acme.co" },
  ],
});
```

### Replace the whole config (PUT)

`PUT /providers/{id}` replaces the config in full. `provider` is required, and every field you omit is cleared, including `alias` and any `settings` key such as `rate_limit`. Use it when you intend to define the complete config, for example from a provisioning script that owns every field. To change one setting, use [PATCH](#update-part-of-a-config-patch).

The body has the same shape as `providers.create`.

### Delete

`client.providers.delete(id)` (`DELETE /providers/{id}`).

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

Set or change it with an `add` operation on `PATCH`, so the rest of the config stays as it is. `add` works whether or not a limit exists:

**TypeScript:**
```typescript
await client.providers.patch("provider_01abc123", {
  patch: [{ op: "add", path: "/settings/rate_limit", value: { rate: 10, period: "second" } }],
});
```

Change only the rate with `{ op: "replace", path: "/settings/rate_limit/rate", value: 5 }`, and remove the limit with `{ op: "remove", path: "/settings/rate_limit" }`.

To start a new config with a limit, include `rate_limit` in `settings` on `providers.create`.

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

For SendGrid and Twilio, `body` merges into that provider's own request (SendGrid `/mail/send`, Twilio `Messages.json`), so use their field names. APNs differs: `body` takes Courier's fields (`payload`, `category`, `content-available`), and `body.aps` replaces the whole `aps` dictionary. Check the provider's integration page before writing `body`.

See [multi-channel.md](./multi-channel.md#provider-failover) for failover semantics and [routing-strategies.md](./routing-strategies.md) for workspace-level provider priority.

---

## Related

- [Routing Strategies](./routing-strategies.md), reference providers in `channels.{channel}.providers`
- [Multi-Channel](./multi-channel.md), failover semantics, per-send `providers.{key}.override`
- [Email](../channels/email.md), [SMS](../channels/sms.md), [Push](../channels/push.md), channel-specific deliverability considerations
- [Create a provider](https://www.courier.com/docs/api-reference/providers/create-a-provider), official endpoint reference
- [List available provider types](https://www.courier.com/docs/api-reference/providers/list-available-provider-types), `/providers/catalog` reference
- [Integrations Overview](https://www.courier.com/docs/integrations/overview), human-facing integration docs
