# Reusable Patterns

Copy-paste implementations for cross-cutting concerns that apply across notification types. Each pattern includes TypeScript, Python, CLI, and/or curl examples.

## Idempotency Keys

Always use idempotency keys for transactional sends. Courier stores keys for 24 hours. See [Reliability](./reliability.md) for full idempotency guidance and key pattern table.

**TypeScript:**
```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_CONFIRMATION",
    data: { orderId: "12345" }
  }
}, {
  idempotencyKey: `order-confirmation-12345`
});
```

**Python:**
```python
from courier.client import Courier

client = Courier()

client.send(
    message={
        "to": {"user_id": "user-123"},
        "template": "ORDER_CONFIRMATION",
        "data": {"orderId": "12345"},
    },
    idempotency_key="order-confirmation-12345",
)
```

**CLI:**
```bash
courier send message \
  --message.to.user_id "user-123" \
  --message.template "ORDER_CONFIRMATION" \
  --message.data '{"orderId": "12345"}'
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
      "template": "ORDER_CONFIRMATION",
      "data": { "orderId": "12345" }
    }
  }'
```

Key pattern: `{notification-type}-{unique-id}`. OTP and password reset keys include a timestamp because they should be sendable multiple times. See [Reliability > Key Patterns](./reliability.md#key-patterns) for the full table.

## Consent Check

Check user consent before sending growth/marketing notifications. Courier auto-checks preferences for templates linked to topics, but verify programmatically when needed.

**TypeScript:**
```typescript
async function hasConsent(userId: string, topic: string): Promise<boolean> {
  try {
    const prefs = await courier.users.preferences.get(userId);
    const topicPref = prefs.topics?.[topic];
    return topicPref?.status === "OPTED_IN";
  } catch {
    return false;
  }
}

if (await hasConsent(userId, "growth-notifications")) {
  await courier.send({ ... });
}
```

**Python:**
```python
def has_consent(user_id: str, topic: str) -> bool:
    try:
        prefs = client.users.preferences.get(user_id)
        topic_pref = next((t for t in prefs.items if t.topic_id == topic), None)
        return topic_pref is not None and topic_pref.status == "OPTED_IN"
    except Exception:
        return False

if has_consent(user_id, "growth-notifications"):
    client.send(message={...})
```

### Consent Record Structure

Store consent records for audit compliance (GDPR, TCPA, CASL):

```typescript
interface ConsentRecord {
  userId: string;
  email?: string;
  phone?: string;
  consentedAt: Date;
  method: "web_form" | "sms_keyword" | "verbal" | "import";
  ipAddress?: string;
  consentText: string;       // Exact text user agreed to
  categories: string[];      // e.g. ["marketing", "product-updates"]
  expiresAt?: Date;          // For implied consent (CASL)
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
    await courier.send(message);
    return;
  }

  if (isQuietHours(timezone)) {
    await queueForLater(userId, message, { deliverAt: "08:00", timezone });
    return;
  }

  await courier.send(message);
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
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "IMPORTANT_UPDATE",
    routing: {
      method: "single",
      channels: ["push", "email", "sms"]
    }
  }
});
```

**Python:**
```python
client.send(
    message={
        "to": {"user_id": "user-123"},
        "template": "IMPORTANT_UPDATE",
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
  --message.to.user_id "user-123" \
  --message.template "IMPORTANT_UPDATE" \
  --message.routing.method "single" \
  --message.routing.channels '["push", "email", "sms"]'
```

**curl:**
```bash
curl -X POST https://api.courier.com/send \
  -H "Authorization: Bearer $COURIER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "to": { "user_id": "user-123" },
      "template": "IMPORTANT_UPDATE",
      "routing": {
        "method": "single",
        "channels": ["push", "email", "sms"]
      }
    }
  }'
```

For critical alerts that send to all channels simultaneously, use `method: "all"`. See [Multi-Channel > All Channels](./multi-channel.md#all-channels-method-all) for examples.

## Webhook Handler

Always respond 200 immediately and process asynchronously. Handle duplicates. See [Reliability > Webhooks](./reliability.md#webhooks) for event types and best practices.

**TypeScript (Express):**
```typescript
app.post("/webhooks/courier", async (req, res) => {
  res.sendStatus(200);

  const { event, messageId } = req.body;

  const alreadyProcessed = await cache.get(`webhook-${messageId}-${event}`);
  if (alreadyProcessed) return;
  await cache.set(`webhook-${messageId}-${event}`, true, { ttl: 86400 });

  await queue.add("process-webhook", req.body);
});
```

**Python (Flask):**
```python
@app.route("/webhooks/courier", methods=["POST"])
def courier_webhook():
    payload = request.get_json()
    event = payload.get("event")
    message_id = payload.get("messageId")

    cache_key = f"webhook-{message_id}-{event}"
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
      await courier.send(message);
      return;
    } catch (error: any) {
      if (error.statusCode >= 400 && error.statusCode < 500) {
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
from courier.client import Courier

def send_with_retry(client: Courier, message: dict, max_attempts: int = 3):
    for attempt in range(max_attempts):
        try:
            return client.send(message=message)
        except Exception as e:
            status = getattr(e, "status_code", 500)
            if 400 <= status < 500:
                raise
            if attempt == max_attempts - 1:
                raise
            delay = min(2 ** attempt, 30) + random.random()
            time.sleep(delay)
```

## Automation Cancellation

Cancel an automation sequence when the user takes the desired action.

**TypeScript:**
```typescript
await courier.automations.invoke("onboarding-sequence", {
  user_id: "user-123",
  cancelation_token: `onboarding-${userId}`,
  data: { userName: "Jane" }
});

// Later, when user activates
await courier.automations.cancel({
  cancelation_token: `onboarding-${userId}`
});
```

**Python:**
```python
client.automations.invoke(
    "onboarding-sequence",
    user_id="user-123",
    cancelation_token=f"onboarding-{user_id}",
    data={"userName": "Jane"},
)

# Later, when user activates
client.automations.cancel(cancelation_token=f"onboarding-{user_id}")
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

## Related

- [CLI](./cli.md) - CLI for ad-hoc operations and debugging
- [Quickstart](./quickstart.md) - Send your first notification
- [Multi-Channel](./multi-channel.md) - Routing strategies
- [Reliability](./reliability.md) - Idempotency and retry details
- [Compliance](./compliance.md) - Legal requirements
- [Throttling](./throttling.md) - Rate limiting details
- [Batching](./batching.md) - Aggregation strategies
- [Preferences](./preferences.md) - User preference management
