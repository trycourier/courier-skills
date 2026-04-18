# Reusable Patterns

Copy-paste implementations for cross-cutting concerns that apply across notification types. Each pattern includes TypeScript, Python, CLI, and/or curl examples.

> **Reading order:** This file is the copy-paste companion. For the **concepts** behind idempotency, webhook handling, retries, and failover — including when to use which pattern and what the failure modes are — read [Reliability](./reliability.md) first, then come back here for code.

## Quick Reference

### Rules
- **Idempotency keys are sent as an `Idempotency-Key` HTTP header**, never inside `message`. In Node pass `{ headers: { "Idempotency-Key": "..." } }` as the second argument to `client.send.message`. In Python pass `extra_headers={"Idempotency-Key": "..."}`. On the REST API use the `Idempotency-Key` header directly. (The Node SDK's `idempotencyKey` request option may not be wired through in all SDK versions — always set the header explicitly to be safe. Verify against your installed `@trycourier/courier` version before relying on any other path. Python does not accept `idempotency_key=` at all.) The CLI does not yet have an `--idempotency-key` flag; for idempotent ad-hoc sends, use the SDK or curl. Keys are valid for 24 hours.
- **Check consent before growth/marketing sends**, not before transactional sends. Transactional notifications (password reset, OTP, receipts, security alerts) bypass marketing consent.
- **Quiet hours apply to non-urgent channels only.** Never delay OTP, password reset, security alerts, or critical account alerts, regardless of time.
- **Throttle checks should be per-user × per-category.** Global throttles are usually wrong — a user's OTP budget is not the same as their marketing budget.
- **Fallback routing (`method: "single"`) tries channels in order until one succeeds.** Use `method: "all"` only for genuinely multi-channel events (order shipped = email + push).
- **Webhook handlers must respond 200 fast** (< 3s) and do work async. Always verify the `courier-signature` header — see [reliability.md](./reliability.md#verify-webhook-signatures).
- **Retry only transient errors** (5xx, network, 429). Don't retry 4xx client errors, and don't retry indefinitely — cap attempts and use exponential backoff with jitter.
- **Aggregate repeated actors** to avoid "Alice liked your post" × 15. Use batching with a 5–30 minute window for social-style notifications.
- **Cancel scheduled messages** with `client.messages.cancel(messageId)` when the triggering condition becomes stale (e.g., cart abandonment after purchase).
- **Mask sensitive data** (emails, phones, card last-4) in notification bodies and templates before rendering. Never pass raw PII into notification content that could be logged, rendered in Inbox, or included in email preview text.
- **Bulk sends need `event`** (required on `client.bulk.createJob`); list/audience sends use `to: { list_id }` or `to: { audience_id }`.
- **Tenant-scoped sends** (B2B multi-tenant) pass `tenant_id` in `message` to pick up per-tenant brand and preference overrides.

### Pattern → when to use it

| Pattern | Use when | Skip when |
|---------|----------|-----------|
| [Idempotency Keys](#idempotency-keys) | Transactional sends where duplicates are harmful (OTP, payment confirmations, security alerts) | Marketing blasts, where a retry should produce a fresh send |
| [Consent Check](#consent-check) | Growth, marketing, weekly-digest sends | Transactional sends — consent is implied by the transaction |
| [Quiet Hours](#quiet-hours) | Non-urgent push, SMS, marketing | OTP, password reset, security alerts, outage notifications |
| [Throttle Check](#throttle-check) | You need per-user per-category frequency caps beyond Courier preferences | Global platform-level rate limiting (Courier handles provider limits) |
| [Multi-Channel Fallback](#multi-channel-fallback) | OTP, critical transactional, anything with a hard SLA | Events where you genuinely want every channel ("order shipped" → `method: "all"`) |
| [Webhook Handler](#webhook-handler) | You need to react to delivery events (bounces, clicks, undeliverable) | You only need to check status on demand (use `client.messages.retrieve`) |
| [Retry with Exponential Backoff](#retry-with-exponential-backoff) | Your ingest path calls `send.message` and must survive 5xx/network errors | Courier-to-provider retries — those are Courier's job |
| [Actor Aggregation](#actor-aggregation) | Social/activity notifications ("Alice liked", "Bob commented") | Transactional — never aggregate critical messages |
| [Automation Cancellation](#automation-cancellation) | Scheduled reminders whose triggering condition can go stale (cart, abandoned signup) | One-shot sends |
| [Data Masking](#data-masking) | Security alerts, change confirmations, any notification with PII in the body | Sends where the PII IS the value (order confirmation needs the address) |
| [Lists and Bulk Sends](#lists-and-bulk-sends) | Audience-scale delivery (newsletters, product-launch digests) | Single-recipient sends |
| [Tenants (Multi-Tenant / B2B)](#tenants-multi-tenant-b2b) | B2B apps where each customer org needs its own branding or preferences | Consumer apps with one brand |

### Common Mistakes
- Putting `Idempotency-Key` **inside** the `message` object instead of sending it as a request header
- Using the same idempotency key for "send OTP" across multiple attempts (a resend should have a distinct key — typically `otp-{userId}-{otpRequestId}`, keyed off the unique id of the OTP request from your own system)
- Checking consent for transactional sends (you'll lock legitimate users out of OTP/password reset)
- Applying quiet hours to security alerts
- Retrying 4xx errors (you'll hit the same validation failure forever)
- Aggregating OTP or security events
- Forgetting `event` on `client.bulk.createJob` (returns 400)
- Verifying webhooks by re-hashing the parsed JSON — always hash the raw request body concatenated with the timestamp, see [reliability.md](./reliability.md#verify-webhook-signatures)

## Idempotency Keys

Always use idempotency keys for transactional sends. Courier stores keys for 24 hours. See [Reliability](./reliability.md) for full idempotency guidance and key pattern table.

**TypeScript:**
```typescript
import Courier from "@trycourier/courier";

const client = new Courier();

await client.send.message({
  message: {
    to: { user_id: "user-123" },
    template: "nt_01kmrbq6ypf25tsge12qek41r0",
    data: { orderId: "12345" }
  }
}, {
  headers: { "Idempotency-Key": `order-confirmation-12345` }
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
    extra_headers={"Idempotency-Key": "order-confirmation-12345"},
)
```

**CLI:** The Courier CLI does not yet support idempotency keys directly on `courier send message`. For idempotent ad-hoc sends, use the SDK (above) or call the REST API directly with curl (below).

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

Key pattern: `{notification-type}-{unique-id}`. For OTP and password reset, the unique id should be the per-request id from your own system (e.g. `otp-{userId}-{otpRequestId}`) — that way a retry of the same request is deduped, but a legitimately new user-initiated request gets a fresh key. See [Reliability > Idempotency Key Patterns](./reliability.md#idempotency-key-patterns) for the full table.

## Consent Check

Check user consent before sending growth/marketing notifications. Courier auto-checks preferences for templates linked to topics, but verify programmatically when needed.

**TypeScript:**
```typescript
async function hasConsent(userId: string, topic: string): Promise<boolean> {
  try {
    const prefs = await client.users.preferences.retrieve(userId);
    const topicPref = prefs.items?.find((p: any) => p.topic_id === topic);
    return topicPref?.status === "OPTED_IN";
  } catch {
    return false;
  }
}

if (await hasConsent(userId, "growth-notifications")) {
  await client.send.message({ ... });
}
```

**Python:**
```python
def has_consent(user_id: str, topic: str) -> bool:
    try:
        prefs = client.users.preferences.retrieve(user_id)
        topic_pref = next((t for t in prefs.items if t.topic_id == topic), None)
        return topic_pref is not None and topic_pref.status == "OPTED_IN"
    except Exception:
        return False

if has_consent(user_id, "growth-notifications"):
    client.send.message(message={...})
```

### Opt-In Record Structure

Store opt-in records so you can prove when and how a user consented:

```typescript
interface OptInRecord {
  userId: string;
  email?: string;
  phone?: string;
  consentedAt: Date;
  method: "web_form" | "sms_keyword" | "verbal" | "import";
  ipAddress?: string;
  consentText: string;       // Exact text user agreed to
  categories: string[];      // e.g. ["marketing", "product-updates"]
  expiresAt?: Date;          // Optional, for time-bound opt-ins
}
```

## Quiet Hours

Never send non-critical notifications during 10pm-8am in the user's local timezone.

**TypeScript:**
```typescript
function isQuietHours(timezone: string): boolean {
  const hour = parseInt(
    new Date().toLocaleString("en-US", {
      timeZone: timezone,
      hour: "numeric",
      hour12: false,
    })
  );
  return hour >= 22 || hour < 8;
}

async function sendWithQuietHours(
  userId: string,
  timezone: string,
  priority: "critical" | "high" | "medium" | "low",
  message: object
): Promise<void> {
  if (priority === "critical") {
    await client.send.message({ message });
    return;
  }

  if (isQuietHours(timezone)) {
    await queueForLater(userId, message, { deliverAt: "08:00", timezone });
    return;
  }

  await client.send.message({ message });
}
```

**Python:**
```python
from datetime import datetime
from zoneinfo import ZoneInfo

def is_quiet_hours(timezone: str) -> bool:
    hour = datetime.now(ZoneInfo(timezone)).hour
    return hour >= 22 or hour < 8
```

## Throttle Check

Enforce per-user notification limits by priority level. See [Throttling](./throttling.md) for full guidance.

```typescript
async function shouldSend(
  userId: string,
  priority: "critical" | "high" | "medium" | "low"
): Promise<boolean> {
  if (priority === "critical") return true;

  const count = await getNotificationCount(userId, "1h");
  const limits: Record<string, number> = {
    high: 20,
    medium: 10,
    low: 5,
  };

  return count < (limits[priority] ?? 10);
}
```

### Recommended Limits by Channel

| Channel | Limit | Window |
|---------|-------|--------|
| Push | 5-10 | Per hour |
| Email | 3-5 | Per day |
| SMS | 2-3 | Per day |
| In-app | 20-50 | Per hour |

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

Always respond 200 immediately and process asynchronously. Handle duplicates. In production, also verify the webhook signature — see [Reliability > Verify Webhook Signatures](./reliability.md#verify-webhook-signatures) for the full pattern.

**TypeScript (Express):**
```typescript
app.post("/webhooks/courier", async (req, res) => {
  res.sendStatus(200);

  const { type, data } = req.body;
  const messageId = data?.id;

  const alreadyProcessed = await cache.get(`webhook-${messageId}-${type}`);
  if (alreadyProcessed) return;
  await cache.set(`webhook-${messageId}-${type}`, true, { ttl: 86400 });

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

    cache_key = f"webhook-{message_id}-{event_type}"
    if cache.get(cache_key):
        return "", 200
    cache.set(cache_key, True, ex=86400)

    queue.enqueue("process_webhook", payload)
    return "", 200
```

## Retry with Exponential Backoff

For retrying failed sends (5xx errors only, never retry 4xx). See [Reliability > Retry Logic](./reliability.md#retry-logic) for full guidance.

**TypeScript:**
```typescript
async function sendWithRetry(
  message: object,
  maxAttempts: number = 3
): Promise<void> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      await client.send.message({ message });
      return;
    } catch (error: any) {
      if (error.status >= 400 && error.status < 500) {
        throw error;
      }
      if (attempt === maxAttempts - 1) {
        throw error;
      }
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise((r) => setTimeout(r, delay + Math.random() * 1000));
    }
  }
}
```

**Python:**
```python
import time
import random
from courier import Courier

def send_with_retry(client: Courier, message: dict, max_attempts: int = 3):
    for attempt in range(max_attempts):
        try:
            return client.send.message(message=message)
        except Exception as e:
            status = getattr(e, "status_code", 500)
            if 400 <= status < 500:
                raise
            if attempt == max_attempts - 1:
                raise
            delay = min(2 ** attempt, 30) + random.random()
            time.sleep(delay)
```

## Actor Aggregation

Format actor names for batched notifications ("Jane and 5 others").

**TypeScript:**
```typescript
function formatActors(names: string[]): string {
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} and ${names[1]}`;
  const remaining = names.length - 2;
  return `${names[0]}, ${names[1]}, and ${remaining} ${remaining === 1 ? "other" : "others"}`;
}
```

**Python:**
```python
def format_actors(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    remaining = len(names) - 2
    noun = "other" if remaining == 1 else "others"
    return f"{names[0]}, {names[1]}, and {remaining} {noun}"
```

## Automation Cancellation

Cancel an automation sequence when the user takes the desired action.

**TypeScript:**
```typescript
await client.automations.invoke.invokeByTemplate("onboarding-sequence", {
  recipient: "user-123",
  data: {
    userName: "Jane",
    cancelation_token: `onboarding-${userId}`
  }
});

// Later, when user activates
await client.automations.invoke.invokeAdHoc({
  recipient: userId,
  automation: {
    steps: [
      { action: "cancel", cancelation_token: `onboarding-${userId}` }
    ]
  }
});
```

**Python:**
```python
client.automations.invoke.invoke_by_template(
    "onboarding-sequence",
    recipient="user-123",
    data={
        "userName": "Jane",
        "cancelation_token": f"onboarding-{user_id}",
    },
)

# Later, when user activates
client.automations.invoke.invoke_ad_hoc(
    recipient=user_id,
    automation={
        "steps": [
            {"action": "cancel", "cancelation_token": f"onboarding-{user_id}"}
        ]
    },
)
```

## Data Masking

Mask sensitive data in notification content. Required for security change notifications.

**TypeScript:**
```typescript
function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  return `${local[0]}${"*".repeat(Math.max(local.length - 2, 1))}${local.slice(-1)}@${domain}`;
}

function maskPhone(phone: string): string {
  return `***-***-${phone.slice(-4)}`;
}

function maskCard(last4: string): string {
  return `****-****-****-${last4}`;
}
```

**Python:**
```python
def mask_email(email: str) -> str:
    local, domain = email.split("@")
    return f"{local[0]}{'*' * max(len(local) - 2, 1)}{local[-1]}@{domain}"

def mask_phone(phone: str) -> str:
    return f"***-***-{phone[-4:]}"

def mask_card(last4: str) -> str:
    return f"****-****-****-{last4}"
```

## Lists and Bulk Sends

Send to groups of users via lists, or use the Bulk API for large audiences.

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

### Bulk API

For large audiences (product launches, monthly digests) where per-user data varies.

The bulk `message` definition **requires `event`** (an event ID or notification ID). You may optionally also pass `template` or `content` (V2 format) to override the content associated with that event.

**TypeScript:**
```typescript
// V1: event required. `event` can be a mapped event ID or a notification ID (nt_...).
const job = await client.bulk.createJob({
  message: { event: "nt_01kmrc0v4q7x1v5d8c2n6w9hj" },
});

// V2: event required, with an explicit template override.
// const job = await client.bulk.createJob({
//   message: {
//     event: "monthly-digest",
//     template: "nt_01kmrc0v4q7x1v5d8c2n6w9hj",
//   },
// });

await client.bulk.addUsers(job.jobId, {
  users: [
    { to: { user_id: "user-1" }, data: { highlights: 12 } },
    { to: { user_id: "user-2" }, data: { highlights: 7 } },
  ],
});

// runJob returns an empty body ("" / None) on success — don't assert on the
// return value. Poll job progress via client.bulk.retrieveJob(job.jobId),
// which returns { job: { enqueued, received, failures, status, definition } }.
await client.bulk.runJob(job.jobId);
const { job: jobStatus } = await client.bulk.retrieveJob(job.jobId);
```

**Python:**
```python
# V1: event required. `event` can be a mapped event ID or a notification ID.
job = client.bulk.create_job(message={"event": "nt_01kmrc0v4q7x1v5d8c2n6w9hj"})

# V2: event required, with an explicit template override.
# job = client.bulk.create_job(message={
#     "event": "monthly-digest",
#     "template": "nt_01kmrc0v4q7x1v5d8c2n6w9hj",
# })

client.bulk.add_users(job.job_id, users=[
    {"to": {"user_id": "user-1"}, "data": {"highlights": 12}},
    {"to": {"user_id": "user-2"}, "data": {"highlights": 7}},
])

# run_job returns an empty response on success — don't assert on the return
# value. Poll job progress via client.bulk.retrieve_job(job.job_id), which
# returns .job.{ enqueued, received, failures, status, definition }.
client.bulk.run_job(job.job_id)
job_status = client.bulk.retrieve_job(job.job_id).job
```

## Tenants (Multi-Tenant / B2B)

Tenants let you scope branding, preferences, and data per customer organization.

`client.tenants.update(tenantID, body)` is a create-or-replace (`PUT`). Tenants reference a brand by `brand_id`; the brand itself (logo, colors) is managed via the Brands API, not inlined on the tenant.

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

## Related

- [CLI](./cli.md) - CLI for ad-hoc operations and debugging
- [Quickstart](./quickstart.md) - Send your first notification
- [Multi-Channel](./multi-channel.md) - Routing strategies
- [Reliability](./reliability.md) - Idempotency and retry details
- [Throttling](./throttling.md) - Rate limiting details
- [Batching](./batching.md) - Aggregation strategies
- [Preferences](./preferences.md) - User preference management
