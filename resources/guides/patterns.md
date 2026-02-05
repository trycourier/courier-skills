# Reusable Patterns

Copy-paste implementations for cross-cutting concerns that apply across notification types.

## Idempotency Keys

Always use idempotency keys for transactional sends. Courier stores keys for 24 hours.

```typescript
import { CourierClient } from "@trycourier/courier";

const courier = new CourierClient();

// Pattern: {notification-type}-{unique-id}
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

### Key Patterns by Type

| Notification | Key Pattern |
|--------------|-------------|
| Order confirmation | `order-confirmation-{orderId}` |
| Password reset | `password-reset-{userId}-{timestamp}` |
| Payment receipt | `payment-receipt-{paymentId}` |
| Shipping update | `shipping-{shipmentId}-{status}` |
| OTP code | `otp-{userId}-{timestamp}` |
| Welcome email | `welcome-{userId}` |
| Security alert | `security-{userId}-{eventType}-{timestamp}` |

OTP and password reset keys include timestamp because they should be sendable multiple times.

## Consent Check

Check user consent before sending growth/marketing notifications. Courier auto-checks preferences for templates linked to topics, but verify programmatically when needed.

```typescript
async function hasConsent(userId: string, topic: string): Promise<boolean> {
  try {
    const prefs = await courier.users.preferences.get(userId);
    const topicPref = prefs.topics?.[topic];
    return topicPref?.status === "OPTED_IN";
  } catch {
    // If preferences can't be fetched, don't send marketing
    return false;
  }
}

// Usage
if (await hasConsent(userId, "growth-notifications")) {
  await courier.send({ ... });
}
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
  // Critical notifications always send immediately
  if (priority === "critical") {
    await courier.send(message);
    return;
  }

  if (isQuietHours(timezone)) {
    // Queue for delivery at 8am local time
    await queueForLater(userId, message, { deliverAt: "08:00", timezone });
    return;
  }

  await courier.send(message);
}
```

## Throttle Check

Enforce per-user notification limits by priority level.

```typescript
async function shouldSend(
  userId: string,
  priority: "critical" | "high" | "medium" | "low"
): Promise<boolean> {
  // Critical notifications always send
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

Standard pattern for sending with fallback channels using `method: "single"`.

```typescript
// Try channels in order until one succeeds
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "IMPORTANT_UPDATE",
    data: { ... },
    routing: {
      method: "single",
      channels: ["push", "email", "sms"]  // Priority order
    }
  }
});
```

### Critical Alert (All Channels)

```typescript
// Send to ALL channels simultaneously for critical notifications
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "SECURITY_ALERT",
    data: { ... },
    routing: {
      method: "all",
      channels: ["email", "push", "sms", "inbox"]
    }
  }
}, {
  idempotencyKey: `security-${userId}-${eventType}-${Date.now()}`
});
```

### Channel-Specific Content Overrides

Adapt message content per channel in a single send call:

```typescript
await courier.send({
  message: {
    to: { user_id: "user-123" },
    template: "ORDER_SHIPPED",
    data: { orderNumber: "12345", carrier: "FedEx", eta: "Thursday" },
    routing: {
      method: "all",
      channels: ["email", "push", "sms"]
    },
    channels: {
      email: {
        override: {
          subject: "Your order #12345 has shipped!"
          // Full HTML with images, tracking details
        }
      },
      push: {
        override: {
          title: "Order shipped!",
          body: "Arriving Thursday. Tap to track.",
          data: { deepLink: "acme://orders/12345" }
        }
      },
      sms: {
        override: {
          body: "Acme: Order #12345 shipped! Arrives Thu. Track: acme.co/t/12345"
        }
      }
    }
  }
});
```

## Webhook Handler

Always respond 200 immediately and process asynchronously. Handle duplicates.

```typescript
app.post("/webhooks/courier", async (req, res) => {
  // Respond immediately — don't block on processing
  res.sendStatus(200);

  const { event, messageId } = req.body;

  // Guard against duplicate webhook deliveries
  const alreadyProcessed = await cache.get(`webhook-${messageId}-${event}`);
  if (alreadyProcessed) return;
  await cache.set(`webhook-${messageId}-${event}`, true, { ttl: 86400 });

  // Process asynchronously
  await queue.add("process-webhook", req.body);
});
```

## Retry with Exponential Backoff

For retrying failed sends (5xx errors only, never retry 4xx).

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
      // Don't retry client errors — fix the request
      if (error.statusCode >= 400 && error.statusCode < 500) {
        throw error;
      }

      // Last attempt — give up
      if (attempt === maxAttempts - 1) {
        throw error;
      }

      // Exponential backoff with jitter
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      await new Promise((r) => setTimeout(r, delay + Math.random() * 1000));
    }
  }
}
```

## Automation Cancellation

Cancel an automation sequence when the user takes the desired action.

```typescript
// Start automation with a cancellation token
await courier.automations.invoke("onboarding-sequence", {
  user_id: "user-123",
  cancelation_token: `onboarding-${userId}`,
  data: { userName: "Jane" }
});

// Later, when user activates — cancel the sequence
await courier.automations.cancel({
  cancelation_token: `onboarding-${userId}`
});
```

## Data Masking

Mask sensitive data in notification content. Required for security change notifications.

```typescript
function maskEmail(email: string): string {
  const [local, domain] = email.split("@");
  return `${local[0]}${"*".repeat(Math.max(local.length - 2, 1))}${local.slice(-1)}@${domain}`;
  // "jane.doe@acme.com" → "j******e@acme.com"
}

function maskPhone(phone: string): string {
  return `***-***-${phone.slice(-4)}`;
  // "+15551234567" → "***-***-4567"
}

function maskCard(last4: string): string {
  return `****-****-****-${last4}`;
}
```

## Related

- [Multi-Channel](./multi-channel.md) - Routing strategies
- [Reliability](./reliability.md) - Idempotency and retry details
- [Compliance](./compliance.md) - Legal requirements
- [Throttling](./throttling.md) - Rate limiting details
- [Batching](./batching.md) - Aggregation strategies
- [Preferences](./preferences.md) - User preference management
