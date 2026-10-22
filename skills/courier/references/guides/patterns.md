# Reusable Patterns

Copy-paste implementations for cross-cutting concerns that apply across notification types. Each pattern includes TypeScript, Python, CLI, and/or curl examples.

> **Reading order:** This file is the copy-paste companion. The **concepts** behind idempotency, webhooks, retries, and failover (when to use which pattern, and the failure modes) live in [Reliability](./reliability.md). Read that first, then come back here for code.

## Quick Reference

### Rules
- **Idempotency keys travel as the `Idempotency-Key` HTTP header**, never inside `message`. In Node pass `"Idempotency-Key": "..."` next to `message`. In Python pass `idempotency_key="..."`. In the CLI pass `--idempotency-key`. With curl, set the header. The Node `idempotencyKey` request option is not wired up, so don't use it. Keys last 25 hours by default. `{ headers: { "Idempotency-Key": … } }` as the second argument (Node) or `extra_headers=` (Python) sends the same header and also works. For a longer expiry use `"x-idempotency-expiration"` / `x_idempotency_expiration=` / `--x-idempotency-expiration`.
- **Delivery windows delay a send to the next allowed hour.** Skip them for time-critical sends (OTP, password reset, security alerts), which are useless once delayed.
- **Frequency caps live in Courier.** [Send limits](https://www.courier.com/docs/send/statuses#send-limits) cap a user, topic, or tenant across all sends. A journey [`throttle` node](./throttling.md) caps one point in one journey, per user, globally, or by a dynamic key. Don't rebuild them app-side.
- **Fallback routing (`method: "single"`) tries channels in order until one succeeds.** Use `method: "all"` only for genuinely multi-channel events (order shipped = email + push).
- **Webhook handlers must respond 2xx within 10 seconds** (Courier's timeout) and do the work async. Always verify the `courier-signature` header. See [webhooks.md](./webhooks.md#verify-webhook-signatures).
- **The SDK already retries transient errors** (`408`/`409`/`429`/`5xx`, with backoff and jitter). Tune `maxRetries` instead of wrapping calls in your own loop. See [Retries](#retries-the-sdk-already-does-this).
- **Aggregate repeated actors** ("Alice liked your post" × 15) with a journey [`batch` node](./batching.md), not an app-side queue. Don't rely on `category_key` to split batches by value.
- **Cancel scheduled messages** with `client.messages.cancel(messageId)` when the triggering condition becomes stale (e.g., cart abandonment after purchase).
- **Many recipients:** send once with `to: { list_id }` or `to: { audience_id }` and Courier fans out server-side. A plain `to` array caps at **500**; above that use a list, an audience, or a [Bulk API job](./bulk.md).
- **Tenant-scoped sends** (B2B multi-tenant) pass `tenant_id` in `message` to pick up per-tenant brand and preference overrides.

### Pattern → when to use it

| Pattern | Use when | Skip when |
|---------|----------|-----------|
| [Idempotency Keys](#idempotency-keys) | Transactional sends where duplicates are harmful (OTP, payment confirmations, security alerts) | Marketing blasts, where a retry should produce a fresh send |
| [Multi-Channel Fallback](#multi-channel-fallback) | OTP, critical transactional, anything with a hard SLA | Events where you genuinely want every channel ("order shipped" → `method: "all"`) |
| [Webhook Handler](#webhook-handler) | You need to react to delivery events (bounces, clicks, undeliverable) | You only need to check status on demand (use `client.messages.retrieve`) |
| [Retries](#retries-the-sdk-already-does-this) | You want to know what the client retries, or need to tune `maxRetries` | Wrapping an SDK call in your own loop, which multiplies attempts |
| [Sequence Cancellation](#sequence-cancellation) | Scheduled reminders whose triggering condition can go stale (cart, abandoned signup) | One-shot sends |
| [Lists and Audience Sends](#lists-and-audience-sends) | Audience-scale delivery (newsletters, product-launch digests) | Single-recipient sends |
| [Bulk API](./bulk.md) | A large ad-hoc recipient set, per-recipient data, or you want job-level progress | The set is already a list or audience; send to it directly |
| [Tenants (Multi-Tenant / B2B)](#tenants-multi-tenant-b2b) | B2B apps where each customer org needs its own branding or preferences | Consumer apps with one brand |

### Common Mistakes
- Putting `Idempotency-Key` **inside** the `message` object instead of sending it as a request header
- Using the same idempotency key for "send OTP" across multiple attempts (a resend should have a distinct key, typically `otp-{userId}-{otpRequestId}`, keyed off the unique id of the OTP request from your own system)
- Retrying 4xx errors (you'll hit the same validation failure forever)
- Verifying webhooks by re-hashing the parsed JSON. Always hash the raw request body concatenated with the timestamp, see [webhooks.md](./webhooks.md#verify-webhook-signatures)

## Idempotency Keys

Always use idempotency keys for transactional sends. Courier stores keys for 25 hours by default. See [Reliability](./reliability.md) for full idempotency guidance and key pattern table.

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { orderId: "12345" }
  },
  "Idempotency-Key": "order-confirmation-12345"
});
```

**Python:**
```python
from courier import Courier

client = Courier()

client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrbq6ypf25tsge12qek41r0",
        "data": {"orderId": "12345"},
    },
    idempotency_key="order-confirmation-12345",
)
```

**CLI:**
```bash
courier send message \
  --message.to '{"user_id":"user-123"}' \
  --message.template nt_01kmrbq6ypf25tsge12qek41r0 \
  --message.data '{"orderId":"12345"}' \
  --idempotency-key order-confirmation-12345
```

**curl:**
```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: order-confirmation-12345" \
  -d '{
    "message": {
      "to": { "user_id": "user-123" },
      "template": "nt_01kmrbq6ypf25tsge12qek41r0",
      "data": { "orderId": "12345" }
    }
  }'
```

Key pattern: `{notification-type}-{unique-id}`. For OTP and password reset, the unique id should be the per-request id from your own system (e.g. `otp-{userId}-{otpRequestId}`). That way a retry of the same request is deduped, but a legitimately new user-initiated request gets a fresh key. See [Reliability > Idempotency Key Patterns](./reliability.md#idempotency-key-patterns) for the full table.

## Multi-Channel Fallback

Standard pattern for sending with fallback channels. See [Multi-Channel](./multi-channel.md) for routing strategies, escalation patterns, and channel-specific formatting.

**TypeScript:**
```typescript
await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrc0n6x9q3v7d1c5n8w2hj",
    routing: {
      method: "single",
      channels: ["push", "email", "sms"]
    }
  }
});
```

**Python:**
```python
client.send.message(
    message={
        "to": {"user_id": "user-123"},
        "template": "nt_01kmrc0n6x9q3v7d1c5n8w2hj",
        "routing": {
            "method": "single",
            "channels": ["push", "email", "sms"],
        },
    }
)
```

**CLI:**
```bash
courier send message \
  --message.to '{"user_id":"user-123"}' \
  --message.template "nt_01kmrc0n6x9q3v7d1c5n8w2hj" \
  --message.routing '{"method":"single","channels":["push","email","sms"]}'
```

**curl:**
```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "to": { "user_id": "user-123" },
      "template": "nt_01kmrc0n6x9q3v7d1c5n8w2hj",
      "routing": {
        "method": "single",
        "channels": ["push", "email", "sms"]
      }
    }
  }'
```

For critical alerts that send to all channels simultaneously, use `method: "all"`. See [Multi-Channel > All Channels](./multi-channel.md#all-channels-method-all) for examples.

## Webhook Handler

Always respond 2xx immediately (Courier's timeout is 10 seconds) and process asynchronously. Handle duplicates by deduping on `data.id` plus status, since `data.id` is the resource id and repeats across a message's events. In production, also verify the webhook signature. See [Webhooks > Verifying Signatures](./webhooks.md#verify-webhook-signatures) for the full pattern.

**TypeScript (Express):**
```typescript
app.post("/webhooks/courier", async (req, res) => {
  res.sendStatus(200);

  const { type, data } = req.body;
  const key = `webhook-${type}-${data?.id}-${data?.status ?? ""}`;

  const alreadyProcessed = await cache.get(key);
  if (alreadyProcessed) return;
  await cache.set(key, true, { ttl: 86400 });

  await queue.add("process-webhook", req.body);
});
```

**Python (Flask):**
```python
@app.route("/webhooks/courier", methods=["POST"])
def courier_webhook():
    payload = request.get_json()
    event_type = payload.get("type")
    message_id = payload.get("data", {}).get("id")

    cache_key = f"webhook-{event_type}-{message_id}-{payload.get('data', {}).get('status', '')}"
    if cache.get(cache_key):
        return "", 200
    cache.set(cache_key, True, ex=86400)

    queue.enqueue("process_webhook", payload)
    return "", 200
```

## Retries (the SDK already does this)

**Don't hand-roll retry around a Courier SDK call.** Both SDKs retry automatically, so wrapping them
in your own loop multiplies attempts: your 3 tries times the SDK's 3 becomes 9 requests for one send.

What the client does out of the box:

| | Behavior |
|---|---|
| Default attempts | `maxRetries: 2`, so up to 3 requests total |
| Retried | `408`, `409`, `429`, any `5xx`, and connection errors |
| Not retried | Other `4xx`. A malformed send fails immediately, as it should |
| Backoff | Exponential from 0.5s, capped at 8s, with up to 25% jitter |
| Server override | Honors `retry-after` / `retry-after-ms`, and an explicit `x-should-retry` header |

Tune it per client or per request instead of writing your own:

```typescript
const client = new Courier({ maxRetries: 4 });            // default 2

await client.send.message({ message }, { maxRetries: 0 }); // disable for one call
```

```python
client = Courier(max_retries=4)

# Per-request, via with_options (message() itself takes no max_retries kwarg)
client.with_options(max_retries=0).send.message(message=...)
```

Your own retry logic belongs one level out: around **your** ingest path, if a send is part of a
larger unit of work that has to survive a process crash. That is a queue or job-runner concern, not
an SDK wrapper. Pair it with an [idempotency key](#idempotency-keys) so a replay doesn't double-send.


## Sequence Cancellation

End a multi-step sequence when the user takes the desired action. With [Journeys](./journeys.md), build exit logic directly into the DAG using branch nodes and exit nodes, the journey checks a condition before each step and exits early when the goal is met.

**Journeys approach (recommended):**

Design the journey with a branch node that checks whether the user has activated before continuing. This makes cancellation part of the flow itself, no external cancel call needed.

These nodes go in the `PUT /journeys/{id}` body once the journey and its templates exist. `POST /journeys` rejects node `id`s (400) and send nodes (422). See [Journeys](./journeys.md#standard-workflow).

```json
{
  "id": "check-activated",
  "type": "fetch",
  "method": "get",
  "url": "https://api.yourapp.com/users/{{user_id}}/status",
  "merge_strategy": "overwrite"
},
{
  "id": "branch-activated",
  "type": "branch",
  "paths": [
    {
      "label": "User activated",
      "conditions": ["data.activated", "is equal", "true"],
      "nodes": [{ "id": "exit-activated", "type": "exit" }]
    }
  ],
  "default": {
    "label": "Continue sequence",
    "nodes": [
      { "id": "send-reminder", "type": "send", "message": { "template": "<template-id>" } },
      { "id": "wait-2d", "type": "delay", "mode": "duration", "duration": "P2D" }
    ]
  }
}
```

See [Journeys](./journeys.md) for the full workflow (create → template → wire → publish → invoke).

Cancel the sequence when the user activates. Set a cancelation token on the journey and call `POST /journeys/cancel`:

```typescript
await client.journeys.cancel({ cancelation_token: `onboarding-${userId}` });
```

See [Journeys, Cancelling Runs](./journeys.md#cancelling-runs).

## Lists and Audience Sends

Send to a group with one call. Courier fans out to every recipient.

### Lists

**TypeScript:**
```typescript
await client.lists.update("beta-testers", { name: "Beta Testers" });

// Add a single user to a list (additive; does not overwrite existing subscribers).
await client.lists.subscriptions.subscribeUser("user-123", { list_id: "beta-testers" });
await client.lists.subscriptions.subscribeUser("user-456", { list_id: "beta-testers" });

// Or replace the full subscriber set in one call:
// await client.lists.subscriptions.subscribe("beta-testers", {
//   recipients: [{ recipientId: "user-123" }, { recipientId: "user-456" }],
// });

await client.send.message({
  message: {
    to: { list_id: "beta-testers" },
    template: "nt_01kmrbs3q6w9x2c5v8n1d4tjh",
    data: { feature: "Design Studio" },
  },
});
```

**Python:**
```python
client.lists.update("beta-testers", name="Beta Testers")

# Add a single user to a list (additive; does not overwrite existing subscribers).
client.lists.subscriptions.subscribe_user("user-123", list_id="beta-testers")
client.lists.subscriptions.subscribe_user("user-456", list_id="beta-testers")

# Or replace the full subscriber set in one call:
# client.lists.subscriptions.subscribe(
#     "beta-testers",
#     recipients=[{"recipientId": "user-123"}, {"recipientId": "user-456"}],
# )

client.send.message(
    message={
        "to": {"list_id": "beta-testers"},
        "template": "nt_01kmrbs3q6w9x2c5v8n1d4tjh",
        "data": {"feature": "Design Studio"},
    }
)
```

Send to multiple lists with a pattern:

```typescript
await client.send.message({
  message: {
    to: { list_pattern: "eng.*" },
    template: "nt_01kmrc1c8x2q6v1d4c7n5j9ht",
  },
});
```

### Many recipients

Three ways to reach a lot of people. Pick by whether the recipient set is already modeled in Courier.

| Approach | Use when | Ceiling |
|---|---|---|
| `to: { list_id }` / `to: { audience_id }` | The set is already a list or audience | None; Courier fans out server-side |
| `to: [ ... ]` (multi-recipient send) | A handful of ad-hoc recipients | **500 recipients**, hard cap |
| [Bulk API](./bulk.md) | A large ad-hoc set, or you want per-recipient data and job-level progress | Ingest in batches of ≤1000 per call |

Send once to a list or audience and let Courier fan out:

```typescript
await client.send.message({
  message: { to: { list_id: "monthly-digest" }, template: "nt_..." },
});
// or: to: { audience_id: "trial-users-no-integration" }
```

The `to` array on a single send is capped at 500. At 501 the send fails with
`400 message.to has 501 recipients. Max is 500`. Above that, use a list, an audience, or a
[Bulk API job](./bulk.md).

To upsert many profiles first, call `client.profiles.create` per user with a bounded worker pool.

<a id="tenants-multi-tenant-b2b"></a>

## Tenants (Multi-Tenant / B2B)

Tenants let you scope branding, preferences, and data per customer organization.

`client.tenants.update(tenantID, body)` is a create-or-replace (`PUT`): fields you leave out (`properties`, `brand_id`, `user_profile`, `default_preferences`) are cleared, and `brand_id: null` returns `400`, so omit it instead. Tenants reference a brand by `brand_id`; the brand itself (logo, colors) is managed via the Brands API, not inlined on the tenant.

**TypeScript:**
```typescript
await client.tenants.update("acme-corp", {
  name: "Acme Corp",
  brand_id: "BRAND_ACME", // optional; omit if you don't use a custom brand
  properties: { plan: "enterprise" },
});

// Associate a user with a tenant (tenant ID is the first arg; user_id goes in the body).
await client.users.tenants.addSingle("acme-corp", { user_id: "user-123" });

await client.send.message({
  message: {
    to: { user_id: "user-123", tenant_id: "acme-corp" },
    template: "nt_01kmrbw4q7x1v5d8c2n6w9hj",
    data: { name: "Jane" },
  },
});
```

**Python:**
```python
client.tenants.update(
    "acme-corp",
    name="Acme Corp",
    brand_id="BRAND_ACME",  # optional; omit if you don't use a custom brand
    properties={"plan": "enterprise"},
)

# Associate a user with a tenant (tenant ID is the first arg; user_id goes in the body).
client.users.tenants.add_single("acme-corp", user_id="user-123")

client.send.message(
    message={
        "to": {"user_id": "user-123", "tenant_id": "acme-corp"},
        "template": "nt_01kmrbw4q7x1v5d8c2n6w9hj",
        "data": {"name": "Jane"},
    }
)
```

When `tenant_id` is included, Courier applies that tenant's `brand_id` (if set) to the rendered template automatically.

### Per-tenant preferences, templates, and CRUD

Beyond `brand_id`, a tenant carries its own preference defaults (`tenants.preferences.items`) and can
override template content per tenant (`tenants.templates`), on top of full tenant CRUD and user
association. The complete SDK surface, with `OPTED_IN`/`OPTED_OUT`/`REQUIRED` statuses,
`parent_tenant_id` inheritance, and method shapes, is in [tenants.md](./tenants.md).

## Related

- [CLI](./cli.md) - CLI for ad-hoc operations and debugging
- [Quickstart](./quickstart.md) - Send your first notification
- [Multi-Channel](./multi-channel.md) - Routing strategies
- [Reliability](./reliability.md) - Idempotency and retry details
- [Throttling](./throttling.md) - Rate limiting details
- [Batching](./batching.md) - Aggregation strategies
- [Preferences](./preferences.md) - User preference management
