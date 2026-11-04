# Routing Strategies

Workspace-level, reusable routing configurations. A routing strategy bundles a `routing` tree (`method` + `channels`), per-channel provider priority, and per-provider overrides into a single object with an `rs_...` ID. Templates reference it via `routing.strategy_id`.

**Contents:** [Quick Reference](#quick-reference) · [Create a Routing Strategy](#create-a-routing-strategy) · [Use a Strategy in a Template](#use-a-strategy-in-a-template) · [List, Retrieve, Replace, Archive](#list-retrieve-replace-archive) · [Message-level routing vs strategy-level routing](#message-level-routing-vs-strategy-level-routing) · [Related](#related)

## Quick Reference

### Rules
- Routing strategy IDs use the `rs_` prefix (e.g., `rs_01abc123`) and are opaque, workspace-scoped values
- `name` and `routing` are the only required fields on create; both `channels` and `providers` are top-level optional fields that default to empty when omitted
- **Channel-level vs provider-level config:** `channels.{channel}.providers` is the **ordered failover list** for a channel (position = priority). The **top-level** `providers` map carries **per-provider** settings (`override`, `if`, `timeouts`, `metadata`) keyed by provider name. You typically use both: `channels.email.providers: ["sendgrid","aws-ses"]` for order, and `providers.sendgrid.override: {...}` for SendGrid-specific config
- Channel and provider `timeouts` need a business tier plan or higher. Below that, create and replace still return `201`/`200` but drop the `timeouts` silently and keep every other field, and sends through the strategy still go out. `GET` the strategy back to confirm the timeouts were kept. On a send, `timeout.channel` and `timeout.provider` return `402` below the business tier, while `timeout.message`, `escalation` and `criteria` work on every plan. See [routing timeouts](https://www.courier.com/docs/send/routing#timeouts)
- `routing.method` is `"single"` (try channels in order until one succeeds) or `"all"` (send to all channels in parallel)
- **Design Studio names these differently.** **Basic** sends on every channel you switch on. **Advanced** has two lists: everything under **Always send to** (at least one channel) sends, and if the last of those fails, Courier tries the channels in the fallback list below it, in order, until one delivers. For Slack, then Teams, then SMS, then email, put Slack under Always send to and the rest, in that order, in the fallback list. Inside a channel, **To the best of** tries providers in order and **To all** sends through every one
- `PUT /routing-strategies/{id}` is a **full replacement**, any field you omit is reset to its default
- `DELETE /routing-strategies/{id}` archives; it returns **409 Conflict** if any notification template still references the strategy. Unlink templates first (point their `routing.strategy_id` at another strategy; `routing: null` leaves the template unsendable by id)
- `GET /routing-strategies` returns metadata only (no `routing`/`channels`/`providers` content). Use `GET /routing-strategies/{id}` for the full document
- Templates and routing strategies are decoupled: one strategy can back many templates, and swapping a strategy's providers reroutes every template pointing at it without republishing

### Common Mistakes
- Confusing the **message-level** `routing` on `send.message` (per-send override) with the **workspace-level** routing strategy (stored object with an `rs_...` ID and referenced by templates)
- Creating a strategy that references a provider key you haven't configured yet via `/providers`, the strategy will save, but sends will skip that provider silently

### SDK shape

| Operation | Node | Python |
|-----------|------|--------|
| Create | `client.routingStrategies.create({ name, routing, channels?, providers?, description?, tags? })` | `client.routing_strategies.create(name=..., routing=..., ...)` |
| List | `client.routingStrategies.list({ cursor?, limit? })` | `client.routing_strategies.list(cursor=..., limit=...)` |
| Retrieve | `client.routingStrategies.retrieve(id)` | `client.routing_strategies.retrieve(id)` |
| Replace | `client.routingStrategies.replace(id, { name, routing, ... })` | `client.routing_strategies.replace(id, name=..., routing=..., ...)` |
| Archive | `client.routingStrategies.archive(id)` | `client.routing_strategies.archive(id)` |
| Templates using it | `client.routingStrategies.listNotifications(id, { cursor?, limit? })` | `client.routing_strategies.list_notifications(id, cursor=..., limit=...)` |

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

### Full, provider priority + per-provider override

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
      timeouts: { provider: 5000, channel: 30000 }, // business tier or higher, dropped silently below it
      override: {
        // channel-level override applied to every provider
      },
      if: "data.locale !== 'ja-JP'" // skip this channel entirely when false
    }
  },
  providers: {
    sendgrid: {
      override: {
        body: { ip_pool_name: "transactional" }
      },
      timeouts: 4000, // business tier or higher, dropped silently below it
      if: "profile.email_verified === true"
    }
  }
});
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

Pass the `rs_...` as `notification.routing: { strategy_id }` on `notifications.create` or `notifications.replace`, then publish. Sends of that template pick up the strategy's routing. The full create strategy → create template → publish → send flow is in [templates.md](./templates.md#full-lifecycle-example).

---

## List, Retrieve, Replace, Archive

### List
Metadata only, no `routing`/`channels`/`providers` payload. Paginated.

**TypeScript:**
```typescript
const { results, paging } = await client.routingStrategies.list({ limit: 50 });
for (const s of results) console.log(s.id, s.name, s.tags);
if (paging.more) {
  const next = await client.routingStrategies.list({ cursor: paging.cursor!, limit: 50 });
}
```

### Retrieve (full document)

**TypeScript:**
```typescript
const strategy = await client.routingStrategies.retrieve("rs_01abc123");
// strategy.routing, strategy.channels, strategy.providers are populated
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

### Archive

**TypeScript:**
```typescript
await client.routingStrategies.archive("rs_01abc123");
```

Returns `204`. Returns `409` if any template still references the strategy. Find them with `client.routingStrategies.listNotifications(id)`, then point each at another strategy with `notifications.replace`. Use `routing: null` only for a template you are retiring: a template with no strategy isn't sendable by id (see [templates.md](./templates.md)).

---

## Message-level `routing` vs strategy-level `routing`

Two different shapes share the `routing` name; don't confuse them.

| Location | Shape | Purpose |
|----------|-------|---------|
| `send.message({ message: { routing: { method, channels } } })` | Inline `method` + `channels` | Per-send override. Replaces the strategy's method and channel list for that send; the strategy's provider order and channel conditions still apply |
| `notifications.create({ notification: { routing: { strategy_id } } })` | `{ strategy_id }` only | Links a template to a stored strategy |
| `routingStrategies.create({ routing: { method, channels } })` | Inline `method` + `channels` | Defines the strategy itself |

Rule of thumb: if you're reaching for `routing` in a `send.message` call repeatedly with the same values, move it into a stored strategy and link it from the template.

---

## Related

- [Templates](./templates.md), `routing.strategy_id` on notification templates
- [Providers](./providers.md), configure the provider integrations referenced by `channels.{channel}.providers`
- [Multi-Channel](./multi-channel.md), routing methods (`single` vs `all`), per-use-case channel priority, failover semantics
- [Create Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/create-routing-strategy), official endpoint reference
- [Replace Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/replace-routing-strategy)
- [Archive Routing Strategy](https://www.courier.com/docs/api-reference/routing-strategies/archive-routing-strategy)
- [Routing strategies (Design Studio)](https://www.courier.com/docs/send/routing-strategies), dashboard equivalent

