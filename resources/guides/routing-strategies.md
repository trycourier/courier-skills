# Routing Strategies

Workspace-level, reusable routing configurations. A routing strategy bundles a `routing` tree (`method` + `channels`), per-channel provider priority, and per-provider overrides into a single object with an `rs_...` ID. Templates reference it via `routing.strategy_id`.

## Quick Reference

### Rules
- Routing strategy IDs use the `rs_` prefix (e.g., `rs_01abc123`) and are opaque, workspace-scoped values
- `name` and `routing` are the only required fields on create; `channels` defaults to empty when omitted. `providers` is nested **inside** each channel entry (e.g., `channels.email.providers`), not a top-level field
- `routing.method` is `"single"` (try channels in order until one succeeds) or `"all"` (send to all channels in parallel)
- `channels.{channel}.providers` is an **ordered** array — position = failover priority (same as dragging providers in the dashboard)
- `PUT /routing-strategies/{id}` is a **full replacement** — any field you omit is reset to its default
- `DELETE /routing-strategies/{id}` archives; it returns **409 Conflict** if any notification template still references the strategy. Unlink templates first (replace their `routing` with a different strategy or `null`)
- `GET /routing-strategies` returns metadata only (no `routing`/`channels`/`providers` content) — use `GET /routing-strategies/{id}` for the full document
- Templates and routing strategies are decoupled: one strategy can back many templates, and swapping a strategy's providers reroutes every template pointing at it without republishing

### Common Mistakes
- Omitting fields on `PUT` and losing `tags`/`description`/`providers` config silently (it's a replace, not a merge)
- Trying to archive a strategy that's still linked to templates (returns 409 — repoint templates first)
- Confusing the **message-level** `routing` on `send.message` (per-send override) with the **workspace-level** routing strategy (stored object with an `rs_...` ID and referenced by templates)
- Forgetting that provider order in `channels.{channel}.providers` determines failover — reordering the array changes which provider gets tried first
- Creating a strategy that references a provider key you haven't configured yet via `/providers` — the strategy will save, but sends will skip that provider silently

### SDK shape

| Operation | Node | Python |
|-----------|------|--------|
| Create | `client.routingStrategies.create({ name, routing, channels?, providers?, description?, tags? })` | `client.routing_strategies.create(name=..., routing=..., ...)` |
| List | `client.routingStrategies.list({ cursor?, limit? })` | `client.routing_strategies.list(cursor=..., limit=...)` |
| Retrieve | `client.routingStrategies.retrieve(id)` | `client.routing_strategies.retrieve(id)` |
| Replace | `client.routingStrategies.replace(id, { name, routing, ... })` | `client.routing_strategies.replace(id, name=..., routing=..., ...)` |
| Archive | `client.routingStrategies.archive(id)` | `client.routing_strategies.archive(id)` |

---

## Create a Routing Strategy

### Minimal

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

const strategy = await client.routingStrategies.create({
  name: "Simple Email",
  routing: { method: "single", channels: ["email"] }
});

const strategyId = strategy.id; // "rs_..."
```

**Python:**
```python
from courier import Courier

client = Courier()

strategy = client.routing_strategies.create(
    name="Simple Email",
    routing={"method": "single", "channels": ["email"]},
)

strategy_id = strategy.id  # "rs_..."
```

**curl:**
```bash
curl -X POST "https://api.courier.com/routing-strategies" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Simple Email",
    "routing": { "method": "single", "channels": ["email"] }
  }'
```

### Full — provider priority + per-provider override

**TypeScript:**
```typescript
const strategy = await client.routingStrategies.create({
  name: "Email via SendGrid",
  description: "Routes email through SendGrid with SES failover",
  tags: ["production", "email"],
  routing: {
    method: "single",
    channels: ["email"]
  },
  channels: {
    email: {
      providers: ["sendgrid", "aws-ses"], // failover order
      timeouts: { provider: 5000, channel: 30000 },
      override: {
        // channel-level override applied to every provider
      },
      if: "data.locale !== 'ja-JP'" // skip this channel entirely when false
    }
  },
  providers: {
    sendgrid: {
      override: {
        ip_pool_name: "transactional"
      },
      timeouts: 4000,
      if: "profile.email_verified === true"
    }
  }
});
```

**Python:**
```python
strategy = client.routing_strategies.create(
    name="Email via SendGrid",
    description="Routes email through SendGrid with SES failover",
    tags=["production", "email"],
    routing={"method": "single", "channels": ["email"]},
    channels={
        "email": {
            "providers": ["sendgrid", "aws-ses"],
            "timeouts": {"provider": 5000, "channel": 30000},
            "override": {},
            "if": "data.locale !== 'ja-JP'",
        }
    },
    providers={
        "sendgrid": {
            "override": {"ip_pool_name": "transactional"},
            "timeouts": 4000,
            "if": "profile.email_verified === true",
        }
    },
)
```

**curl:**
```bash
curl -X POST "https://api.courier.com/routing-strategies" \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email via SendGrid",
    "description": "Routes email through SendGrid with SES failover",
    "tags": ["production", "email"],
    "routing": { "method": "single", "channels": ["email"] },
    "channels": {
      "email": {
        "providers": ["sendgrid", "aws-ses"],
        "timeouts": { "provider": 5000, "channel": 30000 }
      }
    },
    "providers": {
      "sendgrid": { "override": { "ip_pool_name": "transactional" } }
    }
  }'
```

Returns `201` with the full strategy document (including `id`, `created`, `creator`).

### Multi-channel strategy (fallback chain)

```typescript
await client.routingStrategies.create({
  name: "Transactional Fallback",
  routing: {
    method: "single",
    channels: ["email", "sms"] // try email first, SMS if email fails
  },
  channels: {
    email: { providers: ["sendgrid", "aws-ses"] },
    sms: { providers: ["twilio"] }
  }
});
```

### Fan-out strategy (all channels in parallel)

```typescript
await client.routingStrategies.create({
  name: "Critical Security Alert",
  routing: {
    method: "all",
    channels: ["email", "push", "sms", "inbox"]
  },
  channels: {
    email: { providers: ["sendgrid"] },
    push: { providers: ["apn", "firebase-fcm"] },
    sms: { providers: ["twilio"] },
    inbox: { providers: ["courier"] }
  }
});
```

---

## Use a Strategy in a Template

Pass the `rs_...` as `routing.strategy_id` when creating or replacing a notification template.

**TypeScript (end-to-end: create strategy → create template → publish → send):**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

// 1. Create (or look up) a routing strategy
const strategy = await client.routingStrategies.create({
  name: "Orders — email primary, SMS backup",
  routing: { method: "single", channels: ["email", "sms"] },
  channels: {
    email: { providers: ["sendgrid", "aws-ses"] },
    sms: { providers: ["twilio"] }
  }
});

// 2. Create a template that references it
const template = await client.notifications.create({
  notification: {
    name: "Order Shipped",
    tags: ["transactional", "orders"],
    brand: null,
    subscription: null,
    routing: { strategy_id: strategy.id },
    content: {
      version: "2022-01-01",
      elements: [
        { type: "meta", title: "Your order {{order_id}} has shipped" },
        { type: "text", content: "Hi {{name}}, your package is on the way." },
        { type: "action", content: "Track", href: "{{tracking_url}}" }
      ]
    }
  },
  state: "DRAFT"
});

// 3. Publish
await client.notifications.publish(template.id);

// 4. Send — routing is picked up from the linked strategy
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: template.id,
    data: { name: "Jane", order_id: "ORD-9042", tracking_url: "https://ex.co/t/ORD-9042" }
  }
});
```

**Python:**
```python
from courier import Courier

client = Courier()

strategy = client.routing_strategies.create(
    name="Orders — email primary, SMS backup",
    routing={"method": "single", "channels": ["email", "sms"]},
    channels={
        "email": {"providers": ["sendgrid", "aws-ses"]},
        "sms": {"providers": ["twilio"]},
    },
)

template = client.notifications.create(
    notification={
        "name": "Order Shipped",
        "tags": ["transactional", "orders"],
        "brand": None,
        "subscription": None,
        "routing": {"strategy_id": strategy.id},
        "content": {
            "version": "2022-01-01",
            "elements": [
                {"type": "meta", "title": "Your order {{order_id}} has shipped"},
                {"type": "text", "content": "Hi {{name}}, your package is on the way."},
                {"type": "action", "content": "Track", "href": "{{tracking_url}}"},
            ],
        },
    },
    state="DRAFT",
)

client.notifications.publish(template.id)

client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": template.id,
        "data": {"name": "Jane", "order_id": "ORD-9042", "tracking_url": "https://ex.co/t/ORD-9042"},
    }
)
```

---

## List, Retrieve, Replace, Archive

### List
Metadata only — no `routing`/`channels`/`providers` payload. Paginated.

**TypeScript:**
```typescript
const { results, paging } = await client.routingStrategies.list({ limit: 50 });
for (const s of results) console.log(s.id, s.name, s.tags);
if (paging.more) {
  const next = await client.routingStrategies.list({ cursor: paging.cursor!, limit: 50 });
}
```

**Python:**
```python
response = client.routing_strategies.list(limit=50)
for s in response.results:
    print(s.id, s.name, s.tags)
if response.paging.more:
    next_page = client.routing_strategies.list(cursor=response.paging.cursor, limit=50)
```

**curl:**
```bash
curl -s "https://api.courier.com/routing-strategies?limit=50" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

### Retrieve (full document)

**TypeScript:**
```typescript
const strategy = await client.routingStrategies.retrieve("rs_01abc123");
// strategy.routing, strategy.channels, strategy.providers are populated
```

**Python:**
```python
strategy = client.routing_strategies.retrieve("rs_01abc123")
# strategy.routing, strategy.channels, strategy.providers are populated
```

### Replace (full-document PUT)

Like `PUT /notifications/{id}`, this is a replacement. Always read → modify → write back to avoid dropping fields.

**TypeScript:**
```typescript
const current = await client.routingStrategies.retrieve("rs_01abc123");

await client.routingStrategies.replace("rs_01abc123", {
  name: current.name,
  description: current.description,
  tags: current.tags,
  routing: current.routing,
  channels: {
    ...current.channels,
    email: {
      ...current.channels.email,
      providers: ["aws-ses", "sendgrid"] // flip priority
    }
  },
  providers: current.providers
});
```

**Python:**
```python
current = client.routing_strategies.retrieve("rs_01abc123")

client.routing_strategies.replace(
    "rs_01abc123",
    name=current.name,
    description=current.description,
    tags=current.tags,
    routing=current.routing,
    channels={
        **current.channels,
        "email": {
            **current.channels["email"],
            "providers": ["aws-ses", "sendgrid"],  # flip priority
        },
    },
    providers=current.providers,
)
```

### Archive

**TypeScript:**
```typescript
await client.routingStrategies.archive("rs_01abc123");
```

**Python:**
```python
client.routing_strategies.archive("rs_01abc123")
```

**curl:**
```bash
curl -X DELETE "https://api.courier.com/routing-strategies/rs_01abc123" \
  -H "Authorization: Bearer $COURIER_API_KEY"
```

Returns `204`. Returns `409` if any template still references the strategy — repoint those templates first (set their `routing.strategy_id` to a different strategy or set `routing: null`).

---

## Message-level `routing` vs strategy-level `routing`

Two different shapes share the `routing` name; don't confuse them.

| Location | Shape | Purpose |
|----------|-------|---------|
| `send.message({ message: { routing: { method, channels } } })` | Inline `method` + `channels` | Per-send override; wins over the template's strategy for that one send |
| `notifications.create({ notification: { routing: { strategy_id } } })` | `{ strategy_id }` only | Links a template to a stored strategy |
| `routingStrategies.create({ routing: { method, channels } })` | Inline `method` + `channels` | Defines the strategy itself |

Rule of thumb: if you're reaching for `routing` in a `send.message` call repeatedly with the same values, move it into a stored strategy and link it from the template.

---

## Related

- [Templates](./templates.md) — `routing.strategy_id` on notification templates
- [Providers](./providers.md) — configure the provider integrations referenced by `channels.{channel}.providers`
- [Multi-Channel](./multi-channel.md) — routing methods (`single` vs `all`), per-use-case channel priority, failover semantics
- [Create Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/create-routing-strategy) — official endpoint reference
- [Replace Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/replace-routing-strategy)
- [Archive Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/archive-routing-strategy)
- [Routing Configuration (Design Studio)](https://www.courier.com/docs/platform/content/template-designer/routing-configuration) — dashboard equivalent

<!-- Target line budget: <= 500 lines. -->
